import logging
import asyncio
from typing import Optional
from planner import ProxyPlanner
from src.scenarios.booking.booking import BookingScenario
from src.message_broker import MessageBroker
from view import CLIView
from config import CONFIG

logger = logging.getLogger(__name__)


class NLUManager:
    """
    Natural Language Understanding Manager that coordinates processing of user commands
    and manages scenarios execution.
    """

    def __init__(self, config):
        """
        Initialize NLU Manager with configuration and required components.

        Args:
            config: Application configuration object
        """
        self.view = CLIView()
        self.config = config
        self.proxy_planner = ProxyPlanner()
        self.message_broker = MessageBroker()
        self.active_scenario = None
        self._register_scenarios()

    def _register_scenarios(self) -> None:
        """Register all available scenarios with the proxy planner"""
        logger.info("Registering scenarios")
        self.proxy_planner.register_scenario(
            BookingScenario(message_broker=self.message_broker))

    async def _handle_human_requests(self):
        """Background task to monitor and handle human assistance requests"""
        while True:
            try:
                requests = await self.message_broker.check_requests()
                for request in requests:
                    self.view.display_human_request(
                        question=request.question_to_human,
                        options=request.options
                    )
                    response = self.view.get_human_input(
                        options=request.options)
                    await self.message_broker.send_response(
                        request_id=request.request_id,
                        response=response
                    )
            except Exception as e:
                logger.error("Error handling human requests: %s", str(e))
            await asyncio.sleep(0.1)

    async def process_command(self, command: str) -> None:
        """
        Process a single user command by selecting and executing appropriate scenario.

        Args:
            command: User's natural language command
        """
        logger.info("Processing command: %s", command)

        try:
            # Start showing progress
            self.view.start_progress()

            # Get appropriate scenario
            scenario, score = self.proxy_planner.classify_and_select(command)

            if score > 0:
                logger.info("Selected scenario %s with score %f",
                            type(scenario).__name__, score)
                self.active_scenario = scenario
                success = await scenario.execute(command)
                if success:
                    self.view.display_message("Command executed successfully!")
                else:
                    self.view.display_error("Failed to execute command")
            else:
                logger.warning("No suitable scenario found for command")
                self.view.display_message(
                    "I'm not sure how to handle that command")

        except Exception as e:
            logger.error("Error processing command: %s", str(e), exc_info=True)
            self.view.display_error(f"Error: {str(e)}")
        finally:
            self.view.stop_progress()

    async def run(self) -> None:
        """Main execution loop that processes user input while handling human requests"""
        logger.info("Starting NLU Manager")

        try:
            # Initialize message broker
            await self.message_broker.initialize()
            self.view.display_message("Welcome to the Organization Agent")

            # Start human request handler as background task
            request_handler = asyncio.create_task(
                self._handle_human_requests())

            # Main command processing loop
            while True:
                try:
                    command = self.view.get_input()
                    if command.lower() in ['exit', 'quit']:
                        break

                    # Process command
                    await self.process_command(command)

                except KeyboardInterrupt:
                    logger.info("Received shutdown signal")
                    break
                except Exception as e:
                    logger.error("Unexpected error in main loop: %s", str(e),
                                 exc_info=True)
                    self.view.display_error("An unexpected error occurred")

        finally:
            # Clean up
            request_handler.cancel()
            try:
                await request_handler
            except asyncio.CancelledError:
                pass

            await self.message_broker.close_connection()
            self.view.display_message("Shutting down...")
            logger.info("NLU Manager stopped")


def main():
    """Application entry point"""
    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     # format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    manager = NLUManager(config=CONFIG)
    asyncio.run(manager.run())


if __name__ == "__main__":
    main()
