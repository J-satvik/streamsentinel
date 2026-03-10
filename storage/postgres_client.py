import asyncpg
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_URL = "postgresql://sentinel:sentinel123@localhost:5432/streamsentinel"


async def get_connection():
    return await asyncpg.connect(DB_URL)


async def create_tables():
    conn = await get_connection()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          SERIAL PRIMARY KEY,
            host        TEXT NOT NULL,
            timestamp   TIMESTAMP NOT NULL,
            score       FLOAT NOT NULL,
            threshold   FLOAT NOT NULL,
            confidence  FLOAT NOT NULL,
            severity    TEXT NOT NULL,
            ip_entropy  FLOAT,
            error_ratio FLOAT,
            latency_mean FLOAT,
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.close()
    logger.info("Tables ready")


async def save_alert(alert):
    conn = await get_connection()
    await conn.execute("""
        INSERT INTO alerts
            (host, timestamp, score, threshold, confidence, severity,
             ip_entropy, error_ratio, latency_mean)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
    """,
        alert.host,
        alert.timestamp,
        alert.score,
        alert.threshold,
        alert.confidence,
        alert.severity,
        alert.feature_snapshot.get("ip_entropy"),
        alert.feature_snapshot.get("error_ratio"),
        alert.feature_snapshot.get("latency_mean"),
    )
    await conn.close()


async def get_recent_alerts(limit: int = 50):
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT * FROM alerts
        ORDER BY timestamp DESC
        LIMIT $1
    """, limit)
    await conn.close()
    return [dict(r) for r in rows]


async def get_alert_stats():
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT severity, COUNT(*) as count
        FROM alerts
        GROUP BY severity
        ORDER BY count DESC
    """)
    await conn.close()
    return [dict(r) for r in rows]