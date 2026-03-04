from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class RawEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    host: str
    service: str
    method: str                    # GET, POST, etc.
    endpoint: str
    status_code: int
    latency_ms: float
    payload_bytes: int
    ip_address: str
    country_code: str
    user_agent: str
    error_message: Optional[str] = None

    def to_kafka_bytes(self) -> bytes:
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def from_kafka_bytes(cls, data: bytes) -> "RawEvent":
        return cls.model_validate_json(data.decode("utf-8"))