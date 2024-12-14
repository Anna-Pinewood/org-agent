from abc import ABC, abstractmethod
import requests
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class LLMInterface(ABC):
    """Base class for LLM interfaces"""

    @abstractmethod
    def send_request(self, prompt: str) -> dict:
        """Send request to LLM and return response"""
        pass


class RunPodInterface(LLMInterface):
    """RunPod-specific LLM interface implementation"""

    def __init__(self,
                 base_url: str,
                 api_key: str):
        """Initialize RunPod interface with endpoint ID and API key

        Args:
            endpoint_id: RunPod endpoint ID (e.g. "abc123-def4-...")
            api_key: RunPod API key for authentication
        """
        logger.info("Initializing RunPod interface")
        self.endpoint_url = f"{base_url}/run"
        self.healthcheck_url = f"{base_url}/health"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.status_url = base_url + "/status/{}"  # Template for status endpoint

    def get_health_status(self) -> Dict:
        """Get RunPod service health status"""
        logger.debug("Checking RunPod health status")
        try:
            response = requests.get(
                self.healthcheck_url,
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            status = response.json()
            logger.debug(f"Health status received: {status}")
            return status
        except requests.RequestException as e:
            logger.error(f"Health check failed: {str(e)}")
            raise ConnectionError(
                f"Failed to get RunPod health status: {str(e)}")

    def _check_status(self, request_id: str) -> Dict:
        logger.debug(f"Checking request status for ID: {request_id}")
        try:
            response = requests.get(
                self.status_url.format(request_id),
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(
                f"Status check failed for request {request_id}: {str(e)}")
            raise ConnectionError(f"Failed to check request status: {str(e)}")

    def send_request(self, prompt: str) -> str:
        logger.info("Sending request to RunPod")
        # Log first 100 chars of prompt
        logger.debug(f"Prompt: {prompt[:100]}...")

        payload = {
            "input": {
                "prompt": prompt
            }
        }

        try:
            response = requests.post(
                self.endpoint_url,
                headers=self.headers,  # Now using the headers with API key
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Handle queued request
            if data.get('status') == "IN_QUEUE":
                request_id = data.get('id')
                logger.info(f"Request {request_id} queued, waiting 15 seconds")
                if not request_id:
                    raise Exception(
                        "No request ID received for queued request")

                # Wait and check status
                time.sleep(15)
                data = self._check_status(request_id)

            if data.get('status') != "COMPLETED":
                raise Exception(
                    f"RunPod request failed with status: {data.get('status')}")

            logger.info("Request completed successfully")
            # let's return json values
            result = {
                "output": data['output'][0]['choices'][0]['text'],
                "prompt": data['input']['prompt']
            }
            return result

        except requests.Timeout:
            logger.error("Request timed out")
            raise ConnectionError(
                "RunPod endpoint timed out. Please check if service is running.")
        except requests.ConnectionError:
            logger.error("Connection failed")
            raise ConnectionError(
                "Could not connect to RunPod. Please check if service is running.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise Exception(f"Failed to send request to RunPod: {str(e)}")
