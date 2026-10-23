from typing import List, Dict, Any, Optional
import structlog
import chromadb
from chromadb.config import Settings as ChromaSettings
from .embedder import Embedder
from ..config.settings import get_settings

logger = structlog.get_logger(__name__)

COLLECTION_NAMES = ["security", "best_practices", "frameworks", "patterns"]


class RAGRetriever:
    """Retriever client for ChromaDB knowledge bases across domain-specific collections."""

    def __init__(self, embedder: Optional[Embedder] = None):
        settings = get_settings()
        self.settings = settings
        self.embedder = embedder or Embedder()
        self.client = self._init_client()

    def _init_client(self) -> chromadb.ClientAPI:
        """Connect to HTTP Chroma server with fallback to in-memory/ephemeral client."""
        try:
            client = chromadb.HttpClient(
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Verify connectivity
            client.heartbeat()
            logger.info(
                "chromadb_http_connected",
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT,
            )
            return client
        except Exception as e:
            logger.warning(
                "chromadb_http_failed_using_ephemeral",
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT,
                error=str(e),
            )
            return chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))

    def get_or_create_collection(self, collection_name: str):
        """Retrieve collection reference or initialize it if absent."""
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            logger.error("get_or_create_collection_failed", collection=collection_name, error=str(e))
            raise

    async def query(
        self,
        query_text: str,
        collection: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Query a single collection for semantically matching documents.
        Returns a list of dicts with: page_content, source, metadata, distance.
        """
        if not query_text:
            return []

        try:
            query_embedding = await self.embedder.embed_query(query_text)
            coll = self.get_or_create_collection(collection)

            count = coll.count()
            if count == 0:
                return []

            actual_k = min(top_k, count)
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=actual_k,
                include=["documents", "metadatas", "distances"],
            )

            formatted_results: List[Dict[str, Any]] = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for idx, doc in enumerate(docs):
                meta = metas[idx] if idx < len(metas) and metas[idx] else {}
                dist = distances[idx] if idx < len(distances) else None
                formatted_results.append({
                    "page_content": doc,
                    "source": meta.get("source", collection),
                    "metadata": meta,
                    "collection": collection,
                    "distance": dist,
                })

            return formatted_results

        except Exception as e:
            logger.error(
                "rag_query_failed",
                query_text=query_text[:50],
                collection=collection,
                error=str(e),
            )
            return []

    async def query_multiple(
        self,
        query_text: str,
        collections: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Query multiple collections concurrently and return combined, ranked results.
        """
        target_collections = collections or COLLECTION_NAMES
        combined: List[Dict[str, Any]] = []

        for coll_name in target_collections:
            hits = await self.query(query_text, collection=coll_name, top_k=top_k)
            combined.extend(hits)

        # Sort by distance if available (lower distance is better match)
        combined.sort(key=lambda x: x.get("distance") if x.get("distance") is not None else 999.0)
        return combined[: (top_k * len(target_collections))]
