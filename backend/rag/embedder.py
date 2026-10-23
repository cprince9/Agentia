import hashlib
from typing import List, Optional
import structlog
from langchain_openai import OpenAIEmbeddings
from ..config.settings import get_settings

logger = structlog.get_logger(__name__)


class Embedder:
    """Wrapper for text embedding generation with OpenAI embeddings and deterministic fallback."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = "text-embedding-3-small"
        self._client: Optional[OpenAIEmbeddings] = None

        if self.api_key and not self.api_key.startswith("sk-..."):
            try:
                self._client = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=self.api_key,
                )
            except Exception as e:
                logger.warning("embedder_init_fallback", error=str(e))
                self._client = None

    def _fallback_embed(self, text: str, dim: int = 1536) -> List[float]:
        """Generate deterministic pseudo-embedding vector when API key is unavailable."""
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Seed pseudo-random values deterministically
        vec = []
        for i in range(dim):
            byte_val = hash_digest[i % len(hash_digest)]
            norm = (byte_val / 255.0) * 2.0 - 1.0
            vec.append(round(norm, 6))
        return vec

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query string asynchronously."""
        if not text:
            return [0.0] * 1536

        if self._client:
            try:
                return await self._client.aembed_query(text)
            except Exception as e:
                logger.warning("embed_query_failed_using_fallback", error=str(e))

        return self._fallback_embed(text)

    async def embed_documents(self, docs: List[str]) -> List[List[float]]:
        """Embed a list of text documents asynchronously."""
        if not docs:
            return []

        if self._client:
            try:
                return await self._client.aembed_documents(docs)
            except Exception as e:
                logger.warning("embed_documents_failed_using_fallback", error=str(e))

        return [self._fallback_embed(doc) for doc in docs]
