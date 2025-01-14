from abc import ABC, abstractmethod
import json
import logging
import litellm
from config import CONFIG
logger = logging.getLogger(__name__)


class LLMInterface:
    """litellm-based LLM interface implementation"""

    def __init__(self,
                 model_name: str = CONFIG.llm.model_name,
                 llm_api_key: str = CONFIG.llm.api_key,
                 llm_base_url: str = CONFIG.llm.base_url,
                 prompt: str | None = None):
        logger.info("Initializing litellm interface")
        self.model_name = model_name
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.prompt = prompt

    def send_request(self,
                     call_params: dict[str, str] | None = None,
                     prompt: str | None = None,
                     **kwargs) -> litellm.ModelResponse:
        """
        Parameters
        ----------
        call_params : dict[str, str] | None, optional
            Parameters to format prompt variables,
            if empty then set to {}, by default None
        prompt : str | None, optional
            Prompt to send, if empty then set to self.prompt, by default None

        Returns
        -------
        litellm.ModelResponse
        """
        if prompt is None:
            prompt = self.prompt
        if call_params is None:
            call_params = {}
        messages = [{"role": "user",
                    "content": prompt.format(**call_params)}]
        logger.info(
            "Calling model with prompt (300 symbols):\n%s", prompt[:300])
        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            api_key=self.llm_api_key,
            api_base=self.llm_base_url,
            **kwargs
        )
        # logger.info(
        #     "Got response for call_params %s (300 symbols):\n %s...",
        #     str(call_params), response['choices'][0]['message']['content'][:300])
        logger.info("Total cost %s",  litellm.completion_cost(response))
        return response

    @staticmethod
    def get_response_content(response: litellm.ModelResponse) -> str | dict:
        try:
            result = response['choices'][0]['message']['content']
            return json.loads(result)
        except json.JSONDecodeError:
            return result
