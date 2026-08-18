from data_structures import DoublyLinkedList, HashMap


class Subscription:
    """One subscriber and its FIFO message buffer."""

    def __init__(self, subscriber_id):
        self.subscriber_id = subscriber_id
        self.messages = DoublyLinkedList()

    def enqueue(self, message):
        self.messages.insert_back(message)

    def drain(self):
        messages = []
        while not self.messages.is_empty():
            messages.append(self.messages.remove_front())
        return messages


class PubSubChannel:
    """Channel containing ordered subscribers with per-subscriber buffers."""

    def __init__(self, name):
        self.name = name
        self._subscribers = HashMap()
        self._subscriber_order = DoublyLinkedList()

    def subscribe(self, subscriber_id):
        if self._subscribers.contains(subscriber_id):
            return False

        subscription = Subscription(subscriber_id)
        self._subscribers.put(subscriber_id, subscription)
        self._subscriber_order.insert_back(subscription)
        return True

    def publish(self, message):
        for subscription in self._subscriber_order:
            subscription.enqueue(message)
        return self._subscribers.size()

    def drain(self, subscriber_id):
        subscription = self._subscribers.get(subscriber_id)
        if subscription is None:
            return []
        return subscription.drain()

    def subscriber_count(self):
        return self._subscribers.size()


class PubSubManager:
    """In-memory channel bus shared by one or more MiniRedisStore clients."""

    def __init__(self):
        self._channels = HashMap()
        self._subscriber_counts = HashMap()

    def subscribe(self, subscriber_id, channel_name):
        channel = self._channels.get(channel_name)
        if channel is None:
            channel = PubSubChannel(channel_name)
            self._channels.put(channel_name, channel)

        added = channel.subscribe(subscriber_id)
        if added:
            current_count = self._subscriber_counts.get(subscriber_id, 0)
            self._subscriber_counts.put(subscriber_id, current_count + 1)
        return self.subscription_count(subscriber_id)

    def publish(self, channel_name, message):
        channel = self._channels.get(channel_name)
        if channel is None:
            return 0
        return channel.publish(message)

    def read_messages(self, subscriber_id, channel_name):
        """Drain buffered channel messages for a subscriber in publish order."""

        channel = self._channels.get(channel_name)
        if channel is None:
            return []
        return channel.drain(subscriber_id)

    def subscription_count(self, subscriber_id):
        return self._subscriber_counts.get(subscriber_id, 0)

    def channel_subscriber_count(self, channel_name):
        channel = self._channels.get(channel_name)
        if channel is None:
            return 0
        return channel.subscriber_count()
