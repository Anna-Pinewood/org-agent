from typing import List
import logging
from litellm import embedding
from langchain.embeddings.base import Embeddings

logger = logging.getLogger(__name__)


class LiteLLMEmbeddings(Embeddings):
    """
    LiteLLM embeddings interface that works with Langchain.
    Provides a flexible way to use different embedding models through litellm.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs
    ):
        """
        Initialize LiteLLM embeddings interface.

        Args:
            model_name: Name of the embedding model to use
            api_key: Optional API key for the model
            api_base: Optional API base URL
            **kwargs: Additional arguments passed to litellm embedding call
        """
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.additional_kwargs = kwargs
        logger.info("Initialized LiteLLMEmbeddings with model %s", model_name)

    def _get_embedding_kwargs(self) -> dict:
        """Get kwargs for embedding call."""
        kwargs = {"model": self.model_name}

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        kwargs.update(self.additional_kwargs)
        return kwargs

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings, one for each text
        """
        try:
            if not texts:
                return []

            kwargs = self._get_embedding_kwargs()
            response = embedding(
                input=texts,
                **kwargs
            )

            embeddings = [data["embedding"] for data in response["data"]]
            logger.debug(
                "Successfully embedded %d documents with model %s",
                len(texts), self.model_name
            )
            return embeddings

        except Exception as e:
            logger.error(
                "Error embedding documents with model %s: %s",
                self.model_name, str(e)
            )
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Text to embed

        Returns:
            Query embedding
        """
        try:
            kwargs = self._get_embedding_kwargs()
            response = embedding(
                input=[text],  # API expects a list
                **kwargs
            )

            embedding_result = response["data"][0]["embedding"]
            logger.debug(
                "Successfully embedded query text with model %s",
                self.model_name
            )
            return embedding_result

        except Exception as e:
            logger.error(
                "Error embedding query with model %s: %s",
                self.model_name, str(e)
            )
            raise
