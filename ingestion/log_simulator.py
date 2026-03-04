import time
import random
import logging
from faker import Faker
from .producer import KafkaEventProducer
from .schema import RawEvent

fake = Faker()
logger = logging.getLogger(__name__)

SERVICES = ["auth-service", "payment-api", "user-service", "product-api", "gateway"]
ENDPOINTS = ["/login", "/checkout", "/profile", "/search", "/health", "/api/v1/orders"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
COUNTRIES = ["US", "IN", "GB", "DE", "CN", "BR", "AU", "CA", "FR", "JP"]


def make_normal_event(host: str) -> RawEvent:
    """Generates a realistic normal traffic event."""
    status = random.choices([200, 201, 204, 301, 400, 404, 500],
                            weights=[60, 10, 5, 5, 10, 8, 2])[0]
    return RawEvent(
        host=host,
        service=random.choice(SERVICES),
        method=random.choice(METHODS),
        endpoint=random.choice(ENDPOINTS),
        status_code=status,
        latency_ms=random.lognormvariate(3.5, 0.8),   # ~33ms median
        payload_bytes=random.randint(100, 8192),
        ip_address=fake.ipv4(),
        country_code=random.choice(COUNTRIES),
        user_agent=fake.user_agent(),
        error_message="Internal error" if status == 500 else None,
    )


def make_ddos_event(host: str) -> RawEvent:
    """Simulates a DDoS-style burst — high rate, single IP, many 429s."""
    return RawEvent(
        host=host,
        service="gateway",
        method="GET",
        endpoint="/api/v1/orders",
        status_code=random.choice([200, 429]),
        latency_ms=random.uniform(1, 10),    # unnaturally fast
        payload_bytes=random.randint(50, 200),
        ip_address="185.220.101.47",          # same attacker IP
        country_code="RU",
        user_agent="python-requests/2.28.0",
    )


def run_simulator(
    brokers: str,
    topic: str,
    events_per_second: int = 100,
    anomaly_rate: float = 0.05,
    hosts: list[str] = None,
):
    hosts = hosts or ["server-01", "server-02", "server-03"]
    producer = KafkaEventProducer(brokers=brokers, topic=topic)

    logger.info(f"Simulator running: {events_per_second} eps, {anomaly_rate:.0%} anomaly rate")
    interval = 1.0 / events_per_second

    try:
        while True:
            host = random.choice(hosts)
            if random.random() < anomaly_rate:
                event = make_ddos_event(host)
            else:
                event = make_normal_event(host)

            producer.send(event)
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Simulator stopped.")
        producer.flush()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    run_simulator(
        brokers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
        topic=os.getenv("KAFKA_TOPIC_RAW", "raw-events"),
        events_per_second=50,
        anomaly_rate=0.05,
    )