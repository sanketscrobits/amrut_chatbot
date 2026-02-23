"""
Langfuse Observability Configuration (v3 SDK)
=============================================
Centralised module for Langfuse v3 SDK setup.

The Langfuse v3 CallbackHandler reads credentials from env vars automatically:
  LANGFUSE_SECRET_KEY   — your secret key
  LANGFUSE_PUBLIC_KEY   — your public key
  LANGFUSE_BASE_URL     — e.g. https://cloud.langfuse.com (default)

Usage
-----
from src.utils.langfuse_config import get_langfuse_callback, get_langfuse_client

# 1. Automatic tracing via LangChain / LangGraph callbacks:
handler = get_langfuse_callback()
workflow.invoke(state, config={"callbacks": [handler]})

# 2. Add custom metadata to the active trace right after invoke():
langfuse = get_langfuse_client()
if langfuse:
    langfuse.update_current_trace(input=..., output=..., metadata={...})

# 3. Flush on shutdown:
if langfuse:
    langfuse.flush()
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_langfuse_client = None
_langfuse_available = False


def _try_init_client():
    """Initialise the Langfuse singleton client once (lazy)."""
    global _langfuse_client, _langfuse_available

    if _langfuse_client is not None:
        return

    secret = os.environ.get("LANGFUSE_SECRET_KEY", "")
    public = os.environ.get("LANGFUSE_PUBLIC_KEY", "")

    if not secret or not public:
        logger.warning(
            "[Langfuse] LANGFUSE_SECRET_KEY or LANGFUSE_PUBLIC_KEY not set. "
            "Tracing disabled."
        )
        return

    try:
        # Langfuse v3: Langfuse() reads ALL credentials from env vars
        from langfuse import Langfuse 

        _langfuse_client = Langfuse()
        _langfuse_available = True
        logger.info(
            "[Langfuse]  Client initialised (host: %s)",
            os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
        )
    except Exception as exc:
        logger.warning("[Langfuse] ⚠️ Failed to initialise: %s", exc)


def get_langfuse_client():
    """
    Return the singleton Langfuse v3 client.
    Returns None if Langfuse is unconfigured.
    """
    _try_init_client()
    return _langfuse_client


def get_langfuse_callback():
    """
    Return a Langfuse v3 LangChain CallbackHandler.

    In v3 the handler signature is:
        CallbackHandler(*, public_key=None, update_trace=False, trace_context=None)

    Credentials are read from env vars (LANGFUSE_PUBLIC_KEY, etc.) automatically.
    Call ``get_langfuse_client().update_current_trace(...)`` after workflow.invoke()
    to attach session/user/tags/metadata to the trace.

    Returns None if Langfuse is unconfigured (app continues normally).
    """
    _try_init_client()

    if not _langfuse_available:
        return None

    try:
        from langfuse.langchain import CallbackHandler  # noqa: PLC0415

        # v3: no credential args — reads from env vars; no session/tags here
        handler = CallbackHandler()
        return handler
    except Exception as exc:
        logger.warning("[Langfuse]  Failed to create CallbackHandler: %s", exc)
        return None
