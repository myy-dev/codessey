from data_structures import DoublyLinkedList, HashMap
from memory import MemoryManager
from pubsub import PubSubManager
import response
from ttl import TTLManager


OOM_ERROR = "OOM command not allowed when used_memory > 'maxmemory'"
INTEGER_ERROR = "ERR value is not an integer or out of range"


class MiniRedisStore:
    """Execute Mini Redis commands and coordinate all storage policies."""

    def __init__(
        self,
        time_provider=None,
        pubsub_manager=None,
        subscriber_id=None,
    ):
        self._data = HashMap()
        self._lru_list = DoublyLinkedList()
        self._lru_nodes = HashMap()
        self._ttl = TTLManager(time_provider=time_provider)
        self._memory = MemoryManager()
        self._pubsub = (
            pubsub_manager if pubsub_manager is not None else PubSubManager()
        )
        self._subscriber_id = subscriber_id if subscriber_id is not None else object()

    def execute(self, parts):
        """Execute one tokenized command and return its Redis-style response."""

        if len(parts) == 0:
            return None

        command = parts[0].upper()

        if command == "SET":
            return self._execute_set(parts)
        if command == "GET":
            return self._execute_get(parts)
        if command == "DEL":
            return self._execute_del(parts)
        if command == "EXISTS":
            return self._execute_exists(parts)
        if command == "DBSIZE":
            return self._execute_dbsize(parts)
        if command == "KEYS":
            return self._execute_keys(parts)
        if command == "CONFIG":
            return self._execute_config(parts)
        if command == "INFO":
            return self._execute_info(parts)
        if command == "EXPIRE":
            return self._execute_expire(parts)
        if command == "TTL":
            return self._execute_ttl(parts)
        if command == "PUBLISH":
            return self._execute_publish(parts)
        if command == "SUBSCRIBE":
            return self._execute_subscribe(parts)

        return response.error(f"ERR unknown command '{parts[0]}'")

    def _execute_set(self, parts):
        if len(parts) != 3:
            return self._wrong_args("set")

        key = parts[1]
        value = parts[2]
        self._delete_if_expired(key)

        if not self._memory.can_store_entry(key, value):
            return response.error(OOM_ERROR)

        if self._data.contains(key):
            old_value = self._data.get(key)
            self._data.put(key, value)
            self._memory.replace_entry(key, old_value, value)
        else:
            self._data.put(key, value)
            self._memory.add_entry(key, value)

        self._ttl.remove(key)
        self._touch_lru(key)
        self._evict_until_within_limit()

        if self._data.contains(key):
            return response.simple_string("OK")
        return response.error(OOM_ERROR)

    def _execute_get(self, parts):
        if len(parts) != 2:
            return self._wrong_args("get")

        key = parts[1]
        if self._delete_if_expired(key) or not self._data.contains(key):
            return response.nil()

        self._touch_lru(key)
        return response.bulk_string(self._data.get(key))

    def _execute_del(self, parts):
        if len(parts) != 2:
            return self._wrong_args("del")

        key = parts[1]
        self._delete_if_expired(key)
        if not self._data.contains(key):
            return response.integer(0)

        self._delete_key(key)
        return response.integer(1)

    def _execute_exists(self, parts):
        if len(parts) != 2:
            return self._wrong_args("exists")

        key = parts[1]
        if self._delete_if_expired(key) or not self._data.contains(key):
            return response.integer(0)
        return response.integer(1)

    def _execute_dbsize(self, parts):
        if len(parts) != 1:
            return self._wrong_args("dbsize")

        self._purge_expired()
        return response.integer(self._data.size())

    def _execute_keys(self, parts):
        if len(parts) != 1:
            return self._wrong_args("keys")

        self._purge_expired()
        return response.array(self._data.keys())

    def _execute_config(self, parts):
        if len(parts) != 4 or parts[1].upper() != "SET" or parts[2].lower() != "maxmemory":
            return self._wrong_args("config")

        maxmemory = self._parse_non_negative_int(parts[3])
        if maxmemory is None:
            return response.error(INTEGER_ERROR)

        self._memory.set_maxmemory(maxmemory)
        self._evict_until_within_limit()
        return response.simple_string("OK")

    def _execute_info(self, parts):
        if len(parts) != 2 or parts[1].lower() != "memory":
            return self._wrong_args("info")

        self._purge_expired()
        return response.memory_info(
            self._memory.used_memory,
            self._memory.maxmemory,
            self._memory.evicted_keys,
        )

    def _execute_expire(self, parts):
        if len(parts) != 3:
            return self._wrong_args("expire")

        key = parts[1]
        seconds = self._parse_int(parts[2])
        if seconds is None:
            return response.error(INTEGER_ERROR)

        self._delete_if_expired(key)
        if not self._data.contains(key):
            return response.integer(0)

        if seconds <= 0:
            self._delete_key(key)
            return response.integer(1)

        self._ttl.set_expire(key, seconds)
        return response.integer(1)

    def _execute_ttl(self, parts):
        if len(parts) != 2:
            return self._wrong_args("ttl")

        key = parts[1]
        if self._delete_if_expired(key) or not self._data.contains(key):
            return response.integer(-2)
        if not self._ttl.has_expire(key):
            return response.integer(-1)
        return response.integer(self._ttl.ttl(key))

    def _execute_publish(self, parts):
        if len(parts) != 3:
            return self._wrong_args("publish")

        receiver_count = self._pubsub.publish(parts[1], parts[2])
        return response.integer(receiver_count)

    def _execute_subscribe(self, parts):
        if len(parts) != 2:
            return self._wrong_args("subscribe")

        channel = parts[1]
        subscription_count = self._pubsub.subscribe(self._subscriber_id, channel)
        return response.subscription(channel, subscription_count)

    def read_messages(self, channel):
        """Drain this client's buffered messages for a subscribed channel."""

        return self._pubsub.read_messages(self._subscriber_id, channel)

    def _touch_lru(self, key):
        node = self._lru_nodes.get(key)
        if node is None:
            node = self._lru_list.insert_front(key)
            self._lru_nodes.put(key, node)
        else:
            self._lru_list.move_to_front(node)

    def _delete_key(self, key):
        if not self._data.contains(key):
            self._ttl.remove(key)
            node = self._lru_nodes.remove(key)
            if node is not None:
                self._lru_list.remove_node(node)
            return None

        value = self._data.remove(key)
        self._memory.remove_entry(key, value)
        self._ttl.remove(key)
        node = self._lru_nodes.remove(key)
        if node is not None:
            self._lru_list.remove_node(node)
        return value

    def _delete_if_expired(self, key):
        if self._data.contains(key) and self._ttl.is_expired(key):
            self._delete_key(key)
            return True
        return False

    def _purge_expired(self):
        key = self._ttl.pop_expired_key()
        while key is not None:
            self._delete_key(key)
            key = self._ttl.pop_expired_key()

    def _evict_until_within_limit(self):
        # Expired keys are logically absent and must never cause a live key to
        # be counted as evicted. The expiration heap lets us clear them first.
        self._purge_expired()
        while self._memory.over_limit() and not self._lru_list.is_empty():
            key = self._lru_list.tail.data
            self._delete_key(key)
            self._memory.record_eviction()

    def _parse_int(self, value):
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_non_negative_int(self, value):
        parsed = self._parse_int(value)
        if parsed is None or parsed < 0:
            return None
        return parsed

    def _wrong_args(self, command):
        return response.error(f"ERR wrong number of arguments for '{command}' command")
