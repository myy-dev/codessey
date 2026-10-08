from data_structures import DoublyLinkedList, HashMap


class Subscription:
    """구독자 한 명과 FIFO 메시지 버퍼"""

    def __init__(self, subscriber_id):
        """구독자 식별자와 연결 리스트 기반 메시지 버퍼 초기화"""

        self.subscriber_id = subscriber_id
        self.messages = DoublyLinkedList()

    def enqueue(self, message):
        """메시지 버퍼 끝에 새 메시지 추가"""

        self.messages.insert_back(message)

    def drain(self):
        """메시지 버퍼의 모든 메시지 FIFO 순서 반환 및 비우기"""

        messages = []
        while not self.messages.is_empty():
            messages.append(self.messages.remove_front())
        return messages


class PubSubChannel:
    """순서가 보장된 Subscription과 개별 버퍼를 포함하는 PubSubChannel"""

    def __init__(self, name):
        """채널 이름과 구독자 조회·순서 저장 구조 초기화"""

        self.name = name
        self._subscribers = HashMap()
        self._subscriber_order = DoublyLinkedList()

    def subscribe(self, subscriber_id):
        """중복을 제외한 신규 구독자 등록 및 등록 여부 반환"""

        if self._subscribers.contains(subscriber_id):
            return False

        subscription = Subscription(subscriber_id)
        self._subscribers.put(subscriber_id, subscription)
        self._subscriber_order.insert_back(subscription)
        return True

    def publish(self, message):
        """모든 채널 구독자의 개별 버퍼에 메시지 추가"""

        for subscription in self._subscriber_order:
            subscription.enqueue(message)
        return self._subscribers.size()

    def drain(self, subscriber_id):
        """지정 구독자의 채널 메시지 반환 및 버퍼 비우기"""

        subscription = self._subscribers.get(subscriber_id)
        if subscription is None:
            return []
        return subscription.drain()

    def subscriber_count(self):
        """현재 채널 구독자 수 반환"""

        return self._subscribers.size()


class PubSubManager:
    """여러 MiniRedisStore 클라이언트가 공유하는 PubSubManager"""

    def __init__(self):
        """채널 조회와 구독자별 전체 구독 수 저장 구조 초기화"""

        self._channels = HashMap()
        self._subscriber_counts = HashMap()

    def subscribe(self, subscriber_id, channel_name):
        """채널 생성 또는 조회 후 구독자 등록 및 전체 구독 수 반환"""

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
        """지정 채널에 메시지 발행 및 수신 구독자 수 반환"""

        channel = self._channels.get(channel_name)
        if channel is None:
            return 0
        return channel.publish(message)

    def read_messages(self, subscriber_id, channel_name):
        """발행 순서에 따른 구독자 채널 메시지 반환 및 버퍼 비우기"""

        channel = self._channels.get(channel_name)
        if channel is None:
            return []
        return channel.drain(subscriber_id)

    def subscription_count(self, subscriber_id):
        """지정 구독자의 전체 채널 구독 수 반환"""

        return self._subscriber_counts.get(subscriber_id, 0)

    def channel_subscriber_count(self, channel_name):
        """지정 채널의 현재 구독자 수 반환"""

        channel = self._channels.get(channel_name)
        if channel is None:
            return 0
        return channel.subscriber_count()
