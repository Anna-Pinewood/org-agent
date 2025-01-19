from chromadb.config import ChromaClientSettings
from chromadb import HttpClient
from typing import Any, List, Literal
from abc import ABC, abstractmethod
from typing import Any, List
import logging
from langchain_chroma import Chroma
from langchain.schema import Document
from src.memory.models import ProblemSolution, UserPreference
from .embeddings import LiteLLMEmbeddings
from config import CONFIG

logger = logging.getLogger(__name__)

CollectionType = Literal["preferences", "solutions"]


class MemorySystem:
    """Memory system using ChromaDB for storing and retrieving agent memories."""

    def __init__(
        self,
        embedding_model: str = CONFIG.vectorstore.embedding_model,
        api_key: str = CONFIG.vectorstore.api_key,
        api_base: str | None = CONFIG.vectorstore.base_url,
        chroma_host: str = CONFIG.vectorstore.host,
        chroma_port: int = CONFIG.vectorstore.port
    ):
        """
        Initialize memory system with two collections - preferences and solutions.

        Args:
            embedding_model: Model name for embeddings
            api_key: API key for the embedding model
            api_base: Optional API base URL
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
        """
        try:
            # Initialize ChromaDB client
            self.client = HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=ChromaClientSettings(
                    chroma_server_host=chroma_host,
                    chroma_server_http_port=chroma_port
                )
            )

            # Test connection
            self.client.heartbeat()
            logger.info(
                "Successfully connected to ChromaDB at %s:%d",
                chroma_host, chroma_port
            )

            # Initialize embedding function
            self.embeddings = LiteLLMEmbeddings(
                model_name=embedding_model,
                api_key=api_key,
                api_base=api_base
            )

            # Initialize vector stores for each collection
            self.preferences_store = Chroma(
                collection_name="preferences",
                embedding_function=self.embeddings,
                client=self.client
            )
            self.solutions_store = Chroma(
                collection_name="solutions",
                embedding_function=self.embeddings,
                client=self.client
            )
            logger.info("Memory system initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize memory system: %s", str(e))
            raise

    async def store(self,
                    item: UserPreference | ProblemSolution) -> bool:
        """
        Store item in appropriate collection.

        Args:
            item: UserPreference or ProblemSolution to store

        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            # Prepare document
            content = f"{item.header}: {item.text}"
            doc = Document(page_content=content, metadata=item.model_dump())

            # Store in appropriate collection
            if isinstance(item, UserPreference):
                self.preferences_store.add_documents([doc])
                collection = "preferences"
            else:
                self.solutions_store.add_documents([doc])
                collection = "solutions"

            logger.info(
                "Successfully stored %s in %s collection",
                item.__class__.__name__, collection
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to store %s: %s",
                item.__class__.__name__, str(e)
            )
            return False

    async def retrieve(
        self,
        context: str,
        collection: CollectionType,
        limit: int = 5
    ) -> List[UserPreference] | List[ProblemSolution]:
        """
        Retrieve relevant items from specified collection.

        Args:
            context: Query context for similarity search
            collection: Which collection to search ("preferences" or "solutions")
            limit: Maximum number of items to return

        Returns:
            List of relevant items of appropriate type
        """
        try:
            # Select appropriate store and item class
            if collection == "preferences":
                store = self.preferences_store
                item_class = UserPreference
            else:
                store = self.solutions_store
                item_class = ProblemSolution

            # Perform similarity search
            docs = store.similarity_search(context, k=limit)
            items = [item_class(**doc.metadata) for doc in docs]

            logger.info(
                "Retrieved %d items from %s collection for context: %s",
                len(items), collection, context
            )
            return items

        except Exception as e:
            logger.error(
                "Failed to retrieve items from %s collection: %s",
                collection, str(e)
            )
            return []

    async def wipe_collection(self, collection: CollectionType) -> bool:
        """
        Clear all documents from specified collection.

        Args:
            collection: Which collection to clear

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if collection == "preferences":
                self.preferences_store.delete_collection()
                self.preferences_store = Chroma(
                    collection_name="preferences",
                    embedding_function=self.embeddings,
                    client=self.client
                )
            else:
                self.solutions_store.delete_collection()
                self.solutions_store = Chroma(
                    collection_name="solutions",
                    embedding_function=self.embeddings,
                    client=self.client
                )

            logger.info("Successfully wiped %s collection", collection)
            return True

        except Exception as e:
            logger.error(
                "Failed to wipe %s collection: %s",
                collection, str(e)
            )
            return False
