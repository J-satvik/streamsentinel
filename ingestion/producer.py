import json
import logging
from confluent_kafka import Producer
from .schema import RawEvent

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self, brokers: str, topic: str):
        self.topic = topic
        self._producer = Producer({
            "bootstrap.servers": brokers,
            "compression.type": "snappy",
            "batch.num.messages": 1000,
            "linger.ms": 5,
            "acks": "all",
        })

    def send(self, event: RawEvent) -> None:
        self._producer.produce(
            topic=self.topic,
            key=event.host.encode(),
            value=event.to_kafka_bytes(),
            on_delivery=self._delivery_report,
        )
        self._producer.poll(0)

    def flush(self) -> None:
        self._producer.flush()

    @staticmethod
    def _delivery_report(err, msg):
        if err:
            logger.error(f"Delivery failed: {err}")
        else:
            logger.debug(f"Delivered to {msg.topic()} [{msg.partition()}]")