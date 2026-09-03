import logging
from typing import Any
from langgraph.checkpoint.memory import MemorySaver
from app.config import settings

logger = logging.getLogger("hospital_app.agent.memory")

_checkpointer: Any = None
_pool: Any = None

async def get_checkpointer() -> Any:
    global _checkpointer, _pool
    if _checkpointer is not None:
        return _checkpointer

    db_url = settings.SUPABASE_DB_URL
    is_prod = settings.ENVIRONMENT.lower() == "production"

    if is_prod and not db_url:
        logger.critical("CRITICAL: Production startup failed! Direct SUPABASE_DB_URL is required for LangGraph AsyncPostgresSaver.")
        raise RuntimeError("CRITICAL: Production startup failed! SUPABASE_DB_URL is required for LangGraph state checkpointer in production.")

    if db_url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg_pool import AsyncConnectionPool

            _pool = AsyncConnectionPool(conninfo=db_url, max_size=10, open=False, kwargs={"autocommit": True})
            await _pool.open()
            _checkpointer = AsyncPostgresSaver(conn=_pool)
            logger.info("LangGraph AsyncPostgresSaver checkpointer initialized.")
            return _checkpointer
        except Exception as e:
            if is_prod:
                logger.critical(f"CRITICAL: Failed to initialize AsyncPostgresSaver in production: {e}")
                raise RuntimeError(f"CRITICAL: Production checkpointer initialization failed: {e}")
            logger.warning(f"Failed to initialize AsyncPostgresSaver: {e}. Falling back to MemorySaver for local dev.")

    logger.warning("SUPABASE_DB_URL not configured. Using MemorySaver fallback for local development.")
    _checkpointer = MemorySaver()
    return _checkpointer

async def repair_checkpointer_storage():
    """Scans and repairs any stored checkpointer state records with null/invalid message content in Postgres tables."""
    global _pool
    if not _pool:
        logger.info("[MEMORY REPAIR] MemorySaver in use; skipping Postgres checkpointer repair pass.")
        return
    try:
        repaired_count = 0
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name IN ('checkpoints', 'checkpoint_blobs', 'checkpoint_writes')
                """)
                tables = [r[0] for r in await cur.fetchall()]

                if "checkpoints" in tables:
                    await cur.execute("""
                        UPDATE checkpoints 
                        SET checkpoint = REPLACE(REPLACE(checkpoint::text, '"content": null', '"content": "[]"'), '"content":null', '"content": "[]"')::jsonb 
                        WHERE checkpoint::text LIKE '%"content": null%' OR checkpoint::text LIKE '%"content":null%';
                    """)
                    repaired_count += cur.rowcount if cur.rowcount > 0 else 0

                if "checkpoint_writes" in tables:
                    await cur.execute("""
                        UPDATE checkpoint_writes 
                        SET blob = decode(REPLACE(REPLACE(encode(blob, 'escape'), '"content": null', '"content": "[]"'), '"content":null', '"content": "[]"'), 'escape') 
                        WHERE encode(blob, 'escape') LIKE '%"content": null%' OR encode(blob, 'escape') LIKE '%"content":null%';
                    """)
                    repaired_count += cur.rowcount if cur.rowcount > 0 else 0

                if "checkpoint_blobs" in tables:
                    await cur.execute("""
                        UPDATE checkpoint_blobs 
                        SET blob = decode(REPLACE(REPLACE(encode(blob, 'escape'), '"content": null', '"content": "[]"'), '"content":null', '"content": "[]"'), 'escape') 
                        WHERE encode(blob, 'escape') LIKE '%"content": null%' OR encode(blob, 'escape') LIKE '%"content":null%';
                    """)
                    repaired_count += cur.rowcount if cur.rowcount > 0 else 0

                logger.info(f"[MEMORY REPAIR] Checkpointer repair pass completed cleanly. (Repaired {repaired_count} records)")
    except Exception as e:
        logger.warning(f"[MEMORY REPAIR] Checkpointer repair pass finished with notice: {e}")

async def setup_checkpointer():
    cp = await get_checkpointer()
    if hasattr(cp, "setup"):
        try:
            await cp.setup()
            logger.info("LangGraph checkpointer setup completed.")
        except Exception as e:
            logger.error(f"Error during checkpointer setup: {e}")

    await repair_checkpointer_storage()
