import re
import uuid
from typing import List, Dict, Any, Optional
import httpx
import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .embedder import Embedder
from .retriever import RAGRetriever

logger = structlog.get_logger(__name__)


DEFAULT_KNOWLEDGE_ENTRIES = [
    {
        "collection": "security",
        "title": "OWASP Top 10 - Injection & Broken Auth Prevention",
        "content": (
            "OWASP Top 10 Security Guidelines: Always parameterize SQL queries using ORM or bind variables. "
            "Never concatenate raw user strings into database queries or shell commands. "
            "Enforce strict authentication: use argon2/bcrypt for passwords, enforce password complexity, "
            "and utilize secure JWT tokens with expiration and signature verification. "
            "Validate and sanitize all incoming payloads with Pydantic schemas. "
            "Implement rate limiting on all public endpoints to mitigate brute force and DoS attacks."
        ),
        "source": "https://owasp.org/Top10/",
    },
    {
        "collection": "security",
        "title": "OWASP Top 10 - Sensitive Data Exposure & SSRF",
        "content": (
            "Never log sensitive credentials, tokens, or PII. Use environment variables for secrets, "
            "never hardcode credentials in code repositories. "
            "Validate and whitelist allowed target URLs for outbound HTTP requests to prevent Server-Side "
            "Request Forgery (SSRF). Ensure HTTPS with TLS 1.3 is enforced on all external endpoints."
        ),
        "source": "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
    },
    {
        "collection": "best_practices",
        "title": "Python PEP 8 & Async Best Practices",
        "content": (
            "Python engineering standards: Adhere strictly to PEP 8 styling, explicit typing via typing/pydantic, "
            "and PEP 257 docstrings. In async Python (asyncio), never invoke blocking synchronous I/O operations "
            "such as time.sleep, synchronous requests, or standard file I/O inside the event loop; use "
            "asyncio.sleep, httpx.AsyncClient, and aiofiles instead. Structure exceptions using custom domain classes."
        ),
        "source": "https://peps.python.org/pep-0008/",
    },
    {
        "collection": "frameworks",
        "title": "FastAPI & SQLAlchemy 2.0 Async Design",
        "content": (
            "FastAPI Production Standards: Use dependency injection (Depends) for database sessions and security checks. "
            "Utilize SQLAlchemy 2.0 select() style with selectinload / joinedload to prevent N+1 query problems. "
            "Always wrap session commit/rollback in async context managers. Return explicit Pydantic response models "
            "with response_model argument to prevent internal schema leaks."
        ),
        "source": "https://fastapi.tiangolo.com/tutorial/sql-databases/",
    },
    {
        "collection": "patterns",
        "title": "Microservices, Clean Architecture & Event-Driven Patterns",
        "content": (
            "Clean Architecture dictates separation of concerns: domain models are isolated from frameworks. "
            "Service layers coordinate business logic while repository layers manage persistence. "
            "In event-driven architectures, use Redis pub/sub or message queues for asynchronous notifications. "
            "Design idempotency keys for distributed tasks to guarantee safe retries."
        ),
        "source": "https://martinfowler.com/architecture/",
    },
]


class DocumentIngestor:
    """Document ingestion pipeline for populating vector knowledge collections."""

    def __init__(self, retriever: Optional[RAGRetriever] = None, embedder: Optional[Embedder] = None):
        self.retriever = retriever or RAGRetriever()
        self.embedder = embedder or self.retriever.embedder
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def ingest_text(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        collection: str,
    ) -> int:
        """
        Embed and store chunks into the specified ChromaDB collection.
        """
        if not texts:
            return 0

        try:
            coll = self.retriever.get_or_create_collection(collection)
            embeddings = await self.embedder.embed_documents(texts)
            ids = [str(uuid.uuid4()) for _ in texts]

            coll.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info("documents_ingested", collection=collection, count=len(texts))
            return len(texts)
        except Exception as e:
            logger.error("ingest_text_failed", collection=collection, error=str(e))
            raise

    async def ingest_url(self, url: str, collection: str) -> int:
        """
        Fetch URL content via HTTP, strip markup, chunk, embed, and store.
        """
        logger.info("fetching_url_for_ingestion", url=url, collection=collection)
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http_client:
                response = await http_client.get(url)
                response.raise_for_status()
                html = response.text

            # Clean markup to plain text
            text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()

            chunks = self.splitter.split_text(text)
            if not chunks:
                return 0

            metadatas = [{"source": url, "collection": collection, "chunk": i} for i in range(len(chunks))]
            return await self.ingest_text(chunks, metadatas, collection)

        except Exception as e:
            logger.warning("ingest_url_failed", url=url, error=str(e))
            return 0

    async def ingest_default_knowledge_base(self) -> Dict[str, int]:
        """
        Seed the vector database with foundational software engineering standards.
        """
        results: Dict[str, int] = {}
        for entry in DEFAULT_KNOWLEDGE_ENTRIES:
            coll_name = entry["collection"]
            chunks = self.splitter.split_text(entry["content"])
            metas = [{"source": entry["source"], "title": entry["title"]} for _ in chunks]
            count = await self.ingest_text(chunks, metas, coll_name)
            results[coll_name] = results.get(coll_name, 0) + count

        logger.info("default_knowledge_base_seeded", results=results)
        return results
