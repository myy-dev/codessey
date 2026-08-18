import unittest

from parser import ParseError, parse_command
from store import MiniRedisStore


class Clock:
    def __init__(self, value=1000.0):
        self.value = value

    def now(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class ParserTests(unittest.TestCase):
    def test_parse_quoted_value(self):
        self.assertEqual(parse_command('SET greeting "hello world"'), ["SET", "greeting", "hello world"])

    def test_parse_empty_line(self):
        self.assertEqual(parse_command("   "), [])

    def test_parse_unclosed_quote(self):
        with self.assertRaises(ParseError):
            parse_command('SET a "broken')

    def test_parse_escaped_quote(self):
        self.assertEqual(
            parse_command(r'SET greeting "say \"hello\""'),
            ["SET", "greeting", 'say "hello"'],
        )


class StringCommandTests(unittest.TestCase):
    def setUp(self):
        self.store = MiniRedisStore()

    def test_set_get_del_exists_dbsize(self):
        self.assertEqual(self.store.execute(["SET", "name", "alice"]), "OK")
        self.assertEqual(self.store.execute(["GET", "name"]), '"alice"')
        self.assertEqual(self.store.execute(["EXISTS", "name"]), "(integer) 1")
        self.assertEqual(self.store.execute(["DBSIZE"]), "(integer) 1")
        self.assertEqual(self.store.execute(["DEL", "name"]), "(integer) 1")
        self.assertEqual(self.store.execute(["GET", "name"]), "(nil)")
        self.assertEqual(self.store.execute(["EXISTS", "name"]), "(integer) 0")
        self.assertEqual(self.store.execute(["DBSIZE"]), "(integer) 0")

    def test_keys_empty_and_non_empty(self):
        self.assertEqual(self.store.execute(["KEYS"]), "(empty array)")
        self.store.execute(["SET", "a", "1"])
        keys = self.store.execute(["KEYS"])
        self.assertIn('"a"', keys)

    def test_wrong_args_and_unknown_command(self):
        self.assertEqual(
            self.store.execute(["GET"]),
            "(error) ERR wrong number of arguments for 'get' command",
        )
        self.assertEqual(
            self.store.execute(["NOPE"]),
            "(error) ERR unknown command 'NOPE'",
        )

    def test_get_escapes_quotes_backslashes_and_control_characters(self):
        value = 'say "hello"\\next\nline'
        self.store.execute(["SET", "message", value])
        self.assertEqual(
            self.store.execute(["GET", "message"]),
            '"say \\"hello\\"\\\\next\\nline"',
        )


class TTLCommandTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.store = MiniRedisStore(time_provider=self.clock.now)

    def test_expire_and_ttl(self):
        self.store.execute(["SET", "session", "abc"])
        self.assertEqual(self.store.execute(["TTL", "session"]), "(integer) -1")
        self.assertEqual(self.store.execute(["EXPIRE", "session", "10"]), "(integer) 1")
        self.assertEqual(self.store.execute(["TTL", "session"]), "(integer) 10")
        self.clock.advance(11)
        self.assertEqual(self.store.execute(["GET", "session"]), "(nil)")
        self.assertEqual(self.store.execute(["TTL", "session"]), "(integer) -2")

    def test_expire_missing_and_immediate_expire(self):
        self.assertEqual(self.store.execute(["EXPIRE", "missing", "10"]), "(integer) 0")
        self.store.execute(["SET", "temp", "1"])
        self.assertEqual(self.store.execute(["EXPIRE", "temp", "0"]), "(integer) 1")
        self.assertEqual(self.store.execute(["EXISTS", "temp"]), "(integer) 0")

    def test_expire_replaces_old_heap_record(self):
        self.store.execute(["SET", "key", "value"])
        self.store.execute(["EXPIRE", "key", "10"])
        self.clock.advance(5)
        self.store.execute(["EXPIRE", "key", "20"])
        self.clock.advance(6)
        self.assertEqual(self.store.execute(["GET", "key"]), '"value"')


class MemoryAndLRUTests(unittest.TestCase):
    def setUp(self):
        self.store = MiniRedisStore()

    def test_info_memory(self):
        self.store.execute(["SET", "a", "123"])
        self.assertEqual(
            self.store.execute(["INFO", "memory"]),
            "used_memory:4\nmaxmemory:0\nevicted_keys:0",
        )

    def test_lru_eviction(self):
        self.assertEqual(self.store.execute(["CONFIG", "SET", "maxmemory", "6"]), "OK")
        self.assertEqual(self.store.execute(["SET", "a", "11"]), "OK")
        self.assertEqual(self.store.execute(["SET", "b", "22"]), "OK")
        self.assertEqual(self.store.execute(["GET", "a"]), '"11"')
        self.assertEqual(self.store.execute(["SET", "c", "33"]), "OK")
        self.assertEqual(self.store.execute(["GET", "b"]), "(nil)")
        self.assertEqual(self.store.execute(["GET", "a"]), '"11"')
        self.assertEqual(self.store.execute(["GET", "c"]), '"33"')
        self.assertIn("evicted_keys:1", self.store.execute(["INFO", "memory"]))

    def test_oom_for_single_entry_larger_than_maxmemory(self):
        self.store.execute(["CONFIG", "SET", "maxmemory", "3"])
        self.assertEqual(
            self.store.execute(["SET", "long", "value"]),
            "(error) OOM command not allowed when used_memory > 'maxmemory'",
        )
        self.assertEqual(self.store.execute(["DBSIZE"]), "(integer) 0")

    def test_config_rejects_negative_memory(self):
        self.assertEqual(
            self.store.execute(["CONFIG", "SET", "maxmemory", "-1"]),
            "(error) ERR value is not an integer or out of range",
        )


class ExpirationAndLRUIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.store = MiniRedisStore(time_provider=self.clock.now)

    def test_expired_mru_key_does_not_evict_live_lru_key(self):
        self.store.execute(["CONFIG", "SET", "maxmemory", "6"])
        self.store.execute(["SET", "b", "11"])
        self.store.execute(["SET", "a", "22"])
        self.store.execute(["EXPIRE", "a", "1"])

        self.clock.advance(2)
        self.assertEqual(self.store.execute(["SET", "c", "33"]), "OK")

        self.assertEqual(self.store.execute(["GET", "b"]), '"11"')
        self.assertEqual(self.store.execute(["GET", "a"]), "(nil)")
        self.assertIn("evicted_keys:0", self.store.execute(["INFO", "memory"]))

    def test_config_shrink_purges_expired_keys_before_eviction(self):
        self.store.execute(["SET", "live", "1"])
        self.store.execute(["SET", "old", "22"])
        self.store.execute(["EXPIRE", "old", "1"])

        self.clock.advance(2)
        self.assertEqual(
            self.store.execute(["CONFIG", "SET", "maxmemory", "5"]),
            "OK",
        )

        self.assertEqual(self.store.execute(["GET", "live"]), '"1"')
        self.assertIn("evicted_keys:0", self.store.execute(["INFO", "memory"]))


if __name__ == "__main__":
    unittest.main()
