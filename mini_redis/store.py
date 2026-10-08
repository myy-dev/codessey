from data_structures import DoublyLinkedList, HashMap

from . import response
from .memory import MemoryManager
from .pubsub import PubSubManager
from .ttl import TTLManager


OOM_ERROR = "OOM command not allowed when used_memory > 'maxmemory'"
INTEGER_ERROR = "ERR value is not an integer or out of range"


class MiniRedisStore:
    """Mini Redis 명령 실행과 저장소 정책 조정"""

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
        """토큰화된 명령 실행 및 Redis 형식 응답 반환"""

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
        """문자열 키와 값 저장 및 메모리, TTL, LRU 정책 적용"""

        if len(parts) != 3:
            return self._wrong_args("set")

        key = parts[1]
        value = parts[2]
        old_value = self._get_live_value(key)

        if not self._memory.can_store_entry(key, value):
            return response.error(OOM_ERROR)

        self._data.put(key, value)
        if old_value is not None:
            self._memory.replace_entry(key, old_value, value)
        else:
            self._memory.add_entry(key, value)

        self._ttl.remove(key)
        self._touch_lru(key)
        self._evict_until_within_limit()

        if self._data.contains(key):
            return response.simple_string("OK")
        return response.error(OOM_ERROR)

    def _execute_get(self, parts):
        """유효한 값 조회 및 조회 성공 시 LRU 순서 갱신"""

        if len(parts) != 2:
            return self._wrong_args("get")

        key = parts[1]
        value = self._get_live_value(key)
        if value is None:
            return response.nil()

        self._touch_lru(key)
        return response.bulk_string(value)

    def _execute_del(self, parts):
        """키와 관련된 데이터, 메모리, TTL, LRU 정보 삭제"""

        if len(parts) != 2:
            return self._wrong_args("del")

        key = parts[1]
        if self._get_live_value(key) is None:
            return response.integer(0)

        self._delete_key(key)
        return response.integer(1)

    def _execute_exists(self, parts):
        """만료 여부를 반영한 키 존재 여부 반환"""

        if len(parts) != 2:
            return self._wrong_args("exists")

        return response.integer(int(self._get_live_value(parts[1]) is not None))

    def _execute_dbsize(self, parts):
        """만료 키 정리 후 현재 저장된 키 개수 반환"""

        if len(parts) != 1:
            return self._wrong_args("dbsize")

        self._purge_expired()
        return response.integer(self._data.size())

    def _execute_keys(self, parts):
        """만료 키 정리 후 현재 저장된 모든 키 반환"""

        if len(parts) != 1:
            return self._wrong_args("keys")

        self._purge_expired()
        return response.array(self._data.keys())

    def _execute_config(self, parts):
        """최대 메모리 설정 변경 및 필요 시 LRU 키 제거"""

        if len(parts) != 4 or parts[1].upper() != "SET" or parts[2].lower() != "maxmemory":
            return self._wrong_args("config")

        maxmemory = self._parse_non_negative_int(parts[3])
        if maxmemory is None:
            return response.error(INTEGER_ERROR)

        self._memory.set_maxmemory(maxmemory)
        self._evict_until_within_limit()
        return response.simple_string("OK")

    def _execute_info(self, parts):
        """현재 메모리 사용량, 제한, 제거된 키 통계 반환"""

        if len(parts) != 2 or parts[1].lower() != "memory":
            return self._wrong_args("info")

        self._purge_expired()
        return response.memory_info(
            self._memory.used_memory,
            self._memory.maxmemory,
            self._memory.evicted_keys,
        )

    def _execute_expire(self, parts):
        """키의 만료 시간 설정 또는 즉시 만료 처리"""

        if len(parts) != 3:
            return self._wrong_args("expire")

        key = parts[1]
        seconds = self._parse_int(parts[2])
        if seconds is None:
            return response.error(INTEGER_ERROR)

        if self._get_live_value(key) is None:
            return response.integer(0)

        if seconds <= 0:
            self._delete_key(key)
            return response.integer(1)

        self._ttl.set_expire(key, seconds)
        return response.integer(1)

    def _execute_ttl(self, parts):
        """키 만료까지 남은 시간의 초 단위 반환"""

        if len(parts) != 2:
            return self._wrong_args("ttl")

        key = parts[1]
        if self._get_live_value(key) is None:
            return response.integer(-2)
        return response.integer(self._ttl.ttl(key))

    def _execute_publish(self, parts):
        """채널 메시지 발행 및 메시지를 받은 구독자 수 반환"""

        if len(parts) != 3:
            return self._wrong_args("publish")

        receiver_count = self._pubsub.publish(parts[1], parts[2])
        return response.integer(receiver_count)

    def _execute_subscribe(self, parts):
        """현재 클라이언트의 채널 등록 및 전체 구독 수 반환"""

        if len(parts) != 2:
            return self._wrong_args("subscribe")

        channel = parts[1]
        subscription_count = self._pubsub.subscribe(self._subscriber_id, channel)
        return response.subscription(channel, subscription_count)

    def read_messages(self, channel):
        """구독 채널에 쌓인 현재 클라이언트의 메시지 조회 및 비우기"""

        return self._pubsub.read_messages(self._subscriber_id, channel)

    def _touch_lru(self, key):
        """키의 LRU 목록 맨 앞 이동 또는 신규 등록"""

        node = self._lru_nodes.get(key)
        if node is None:
            node = self._lru_list.insert_front(key)
            self._lru_nodes.put(key, node)
        else:
            self._lru_list.move_to_front(node)

    def _delete_key(self, key):
        """키와 연결된 데이터, 메모리, TTL, LRU 상태 제거"""

        value = self._data.remove(key)
        if value is not None:
            self._memory.remove_entry(key, value)
        self._ttl.remove(key)
        node = self._lru_nodes.remove(key)
        if node is not None:
            self._lru_list.remove_node(node)
        return value

    def _get_live_value(self, key):
        """만료 키 정리 및 유효한 문자열 값 또는 None 반환"""

        value = self._data.get(key)
        if value is not None and self._ttl.is_expired(key):
            self._delete_key(key)
            return None
        return value

    def _purge_expired(self):
        """TTL 힙에서 현재 시각까지 만료된 키 제거"""

        key = self._ttl.pop_expired_key()
        while key is not None:
            self._delete_key(key)
            key = self._ttl.pop_expired_key()

    def _evict_until_within_limit(self):
        """메모리 제한 충족까지 만료 키와 LRU 키 제거"""

        # LRU eviction(강제 제거) 전 만료 키 정리 및 강제 제거 통계 제외
        self._purge_expired()
        while self._memory.over_limit() and not self._lru_list.is_empty():
            key = self._lru_list.tail.data
            self._delete_key(key)
            self._memory.record_eviction()

    def _parse_int(self, value):
        """문자열의 정수 변환 및 실패 시 None 반환"""

        try:
            return int(value)
        except ValueError:
            return None

    def _parse_non_negative_int(self, value):
        """문자열의 0 이상 정수 변환 및 실패 시 None 반환"""

        parsed = self._parse_int(value)
        if parsed is None or parsed < 0:
            return None
        return parsed

    def _wrong_args(self, command):
        """명령 인자 개수 오류의 Redis 형식 반환"""

        return response.error(f"ERR wrong number of arguments for '{command}' command")
