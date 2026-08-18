import unittest

from pubsub import PubSubManager
from store import MiniRedisStore


class PubSubCommandTests(unittest.TestCase):
    def setUp(self):
        self.pubsub = PubSubManager()
        self.alice = MiniRedisStore(
            pubsub_manager=self.pubsub,
            subscriber_id="alice",
        )
        self.bob = MiniRedisStore(
            pubsub_manager=self.pubsub,
            subscriber_id="bob",
        )
        self.publisher = MiniRedisStore(pubsub_manager=self.pubsub)

    def test_subscribe_publish_and_read_per_subscriber_buffers(self):
        self.assertEqual(
            self.alice.execute(["SUBSCRIBE", "news"]),
            '1) "subscribe"\n2) "news"\n3) (integer) 1',
        )
        self.assertEqual(
            self.alice.execute(["SUBSCRIBE", "alerts"]),
            '1) "subscribe"\n2) "alerts"\n3) (integer) 2',
        )
        self.assertEqual(
            self.bob.execute(["SUBSCRIBE", "news"]),
            '1) "subscribe"\n2) "news"\n3) (integer) 1',
        )

        self.assertEqual(
            self.publisher.execute(["PUBLISH", "news", "first"]),
            "(integer) 2",
        )
        self.assertEqual(
            self.publisher.execute(["PUBLISH", "news", "second"]),
            "(integer) 2",
        )
        self.assertEqual(
            self.publisher.execute(["PUBLISH", "alerts", "warning"]),
            "(integer) 1",
        )
        self.assertEqual(self.alice.read_messages("news"), ["first", "second"])
        self.assertEqual(self.bob.read_messages("news"), ["first", "second"])
        self.assertEqual(self.alice.read_messages("news"), [])
        self.assertEqual(self.alice.read_messages("alerts"), ["warning"])
        self.assertEqual(self.bob.read_messages("alerts"), [])

    def test_duplicate_subscription_is_idempotent(self):
        first_response = self.alice.execute(["SUBSCRIBE", "news"])
        second_response = self.alice.execute(["SUBSCRIBE", "news"])

        self.assertEqual(second_response, first_response)
        self.assertEqual(self.pubsub.channel_subscriber_count("news"), 1)
        self.assertEqual(self.pubsub.subscription_count("alice"), 1)

    def test_publish_without_subscribers_and_wrong_arguments(self):
        self.assertEqual(
            self.publisher.execute(["PUBLISH", "missing", "message"]),
            "(integer) 0",
        )
        self.assertEqual(
            self.publisher.execute(["PUBLISH", "channel"]),
            "(error) ERR wrong number of arguments for 'publish' command",
        )
        self.assertEqual(
            self.alice.execute(["SUBSCRIBE"]),
            "(error) ERR wrong number of arguments for 'subscribe' command",
        )


if __name__ == "__main__":
    unittest.main()
