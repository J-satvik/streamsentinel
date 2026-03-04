import time
import json
import logging
from collections import defaultdict
from confluent_kafka import Consumer, KafkaError
from ingestion.schema import RawEvent
from inference.engine import InferenceEngine
from inference.scorer import Scorer
from inference.alerter import ConsoleAlerter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

WINDOW_SIZE   = 100   # events per window per host
KAFKA_BROKERS = "localhost:9092"
TOPIC         = "raw-events"
GROUP_ID      = "inference-worker"


class InferenceWorker:
    def __init__(self):
        self.engine  = InferenceEngine()
        self.scorer  = Scorer(self.engine)
        self.alerter = ConsoleAlerter()

        self.consumer = Consumer({
            "bootstrap.servers": KAFKA_BROKERS,
            "group.id":          GROUP_ID,
            "auto.offset.reset": "latest",
        })
        self.consumer.subscribe([TOPIC])

        # rolling buffer per host
        self.buffers = defaultdict(list)
        logger.info(f"Worker started — listening on '{TOPIC}'")
        logger.info(f"Threshold: {self.engine.threshold:.5f}")

    def run(self):
        processed = 0
        alerts     = 0

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    event = RawEvent.from_kafka_bytes(msg.value())
                    self.buffers[event.host].append(event)
                    processed += 1

                    # score when buffer hits window size
                    if len(self.buffers[event.host]) >= WINDOW_SIZE:
                        window = self.buffers[event.host][-WINDOW_SIZE:]
                        alert  = self.scorer.evaluate(window, event.host)

                        if alert:
                            alerts += 1
                            self.alerter.dispatch(alert)

                        # slide window — keep last 50 events
                        self.buffers[event.host] = self.buffers[event.host][-50:]

                    if processed % 500 == 0:
                        logger.info(f"Processed {processed} events | Alerts fired: {alerts}")

                except Exception as e:
                    logger.warning(f"Failed to process message: {e}")

        except KeyboardInterrupt:
            logger.info(f"Worker stopped. Total: {processed} events, {alerts} alerts")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    worker = InferenceWorker()
    worker.run()