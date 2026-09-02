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

            _pool = AsyncConnectionPool(conninfo=db_url, max_size=10, kwargs={"autocommit": True})
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

async def setup_checkpointer():
    cp = await get_checkpointer()
    if hasattr(cp, "setup"):
        try:
            await cp.setup()
            logger.info("LangGraph checkpointer setup completed.")
        except Exception as e:
            logger.error(f"Error during checkpointer setup: {e}")
