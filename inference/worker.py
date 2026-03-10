import time
import logging
from collections import defaultdict
from confluent_kafka import Consumer, KafkaError
from ingestion.schema import RawEvent
from inference.engine import InferenceEngine
from inference.scorer import Scorer
from inference.alerter import ConsoleAlerter
from observability.metrics import (
    RECONSTRUCTION_ERROR, ALERTS_TOTAL,
    EVENTS_PROCESSED, SCORE_HISTOGRAM,
    ANOMALY_ACTIVE, start_metrics_server
)
from storage.postgres_client import save_alert
import asyncio


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

WINDOW_SIZE   = 100
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
        self.buffers = defaultdict(list)

        logger.info(f"Worker started — listening on '{TOPIC}'")
        logger.info(f"Threshold: {self.engine.threshold:.5f}")

    def run(self):
        processed = 0
        alerts    = 0

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

                    # update prometheus
                    EVENTS_PROCESSED.labels(host=event.host).inc()
                    processed += 1

                    if len(self.buffers[event.host]) >= WINDOW_SIZE:
                        window = self.buffers[event.host][-WINDOW_SIZE:]
                        alert  = self.scorer.evaluate(window, event.host)

                        # get raw score for metrics even if no alert
                        from features.extractor import extract
                        fv  = extract(window, event.host)
                        res = self.engine.score(fv.to_vector())

                        # record metrics
                        RECONSTRUCTION_ERROR.labels(host=event.host).set(res["score"])
                        SCORE_HISTOGRAM.observe(res["score"])

                        if alert:
                            alerts += 1
                            ALERTS_TOTAL.labels(
                                host=event.host,
                                severity=alert.severity
                            ).inc()
                            ANOMALY_ACTIVE.labels(host=event.host).set(1)
                            self.alerter.dispatch(alert)

                            # persist to postgres
                            try:
                                asyncio.run(save_alert(alert))
                            except Exception as e:
                                logger.warning(f"Failed to save alert to DB: {e}")
                        else:
                            ANOMALY_ACTIVE.labels(host=event.host).set(0)

                        self.buffers[event.host] = self.buffers[event.host][-50:]

                    if processed % 500 == 0:
                        logger.info(
                            f"Processed {processed} events | Alerts fired: {alerts}"
                        )

                except Exception as e:
                    logger.warning(f"Failed to process message: {e}")

        except KeyboardInterrupt:
            logger.info(f"Worker stopped. Total: {processed} events, {alerts} alerts")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    start_metrics_server(port=8001)
    worker = InferenceWorker()
    worker.run()