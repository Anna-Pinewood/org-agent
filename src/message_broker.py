import logging
import json
import uuid
from typing import Optional, List
import redis.asyncio as redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HumanRequest:
    """Container for human request data"""
    request_id: str
    question_to_human: str
    options: Optional[List[str]] = None


class MessageBroker:
    """Handles async communication between agent and human"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize message broker with Redis connection"""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._request_stream = "human_requests"
        self._response_stream = "human_responses"
        self._consumer_group = "agent_group"
        self._consumer_name = str(uuid.uuid4())

    async def initialize(self):
        """Initialize Redis connection and ensure streams exist"""
        logger.info("Initializing MessageBroker with Redis at %s",
                    self.redis_url)
        self.redis_client = redis.from_url(self.redis_url)

        # Ensure consumer groups exist
        for stream in [self._request_stream, self._response_stream]:
            try:
                await self.redis_client.xgroup_create(
                    stream, self._consumer_group, mkstream=True)
                logger.info("Created consumer group %s for stream %s",
                            self._consumer_group, stream)
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(
                        "Consumer group %s already exists for stream %s",
                        self._consumer_group, stream
                    )
                else:
                    raise

    async def send_request(
        self,
        question: str,
        options: Optional[List[str]] = None,
        scenario_id: Optional[str] = None
    ) -> str:
        """
        Send a request for human input

        Args:
            question: Question to ask human
            options: Optional list of valid choices
            scenario_id: Optional scenario identifier

        Returns:
            str: Generated request ID
        """
        if not self.redis_client:
            raise RuntimeError("MessageBroker not initialized")

        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "scenario_id": scenario_id,
            "question": question,
            "options": options
        }

        logger.info(
            "Sent human request %s for scenario %s: %s",
            request_id, scenario_id, question
        )

        await self.redis_client.xadd(
            self._request_stream,
            {
                "message": json.dumps(message)
            }
        )

        return request_id

    async def send_response(self, request_id: str, response: str):
        """Send response to a human request"""
        if not self.redis_client:
            raise RuntimeError("MessageBroker not initialized")

        message = {
            "request_id": request_id,
            "response": response
        }

        logger.info("Sending response for request %s: %s",
                    request_id, response)

        await self.redis_client.xadd(
            self._response_stream,
            {
                "message": json.dumps(message)
            }
        )

    async def get_response(self, request_id: str) -> Optional[str]:
        """
        Get response for a specific request if available

        Args:
            request_id: ID of the request to check

        Returns:
            Optional[str]: Response if available, None otherwise
        """
        if not self.redis_client:
            raise RuntimeError("MessageBroker not initialized")

        # Read all messages from response stream for this consumer
        messages = await self.redis_client.xread(
            {self._response_stream: "0-0"},
            block=100
        )

        if not messages:
            return None

        # Process messages
        for _, message_list in messages:
            for message_id, message_data in message_list:
                try:
                    # Handle byte string conversion properly
                    if b'message' in message_data:
                        message_str = message_data[b'message'].decode('utf-8')
                        message = json.loads(message_str)
                        if message["request_id"] == request_id:
                            logger.debug(
                                "Found response for request %s", request_id)
                            return message["response"]
                except Exception as e:
                    logger.error("Error parsing message data: %s - %s",
                                 str(message_data), str(e))

        return None

    async def check_requests(self) -> List[HumanRequest]:
        """Check for pending human requests"""
        if not self.redis_client:
            raise RuntimeError("MessageBroker not initialized")

        # Read new messages from request stream
        messages = await self.redis_client.xreadgroup(
            self._consumer_group,
            self._consumer_name,
            {self._request_stream: ">"},
            block=100
        )

        requests = []
        if messages:
            for stream_name, message_list in messages:
                for message_id, message_data in message_list:
                    try:
                        if b'message' in message_data:
                            message_str = message_data[b'message'].decode(
                                'utf-8')
                            message = json.loads(message_str)
                            request_id = message["request_id"]
                            logger.debug(
                                "Found pending request %s: %s",
                                request_id, message["question"]
                            )
                            requests.append(HumanRequest(
                                request_id=request_id,
                                question_to_human=message["question"],
                                options=message.get("options")
                            ))
                    except Exception as e:
                        logger.error("Error parsing request message data: %s - %s",
                                     str(message_data), str(e))

        return requests

    async def close_connection(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
