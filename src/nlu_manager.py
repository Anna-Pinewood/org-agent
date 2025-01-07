import logging
from typing import Optional
import redis
from planner import ProxyPlanner
from scenarios.booking import BookingScenario
from view import CLIView
from config import CONFIG

logger = logging.getLogger(__name__)


class NLUManager:
    def __init__(self, config):
        self.view = CLIView()
        self.config = config
        self.proxy_planner = ProxyPlanner()
        self._register_scenarios()
        # self.redis_client = self._init_redis()
        self.active_scenario = None

    def _register_scenarios(self):
        """Register all available scenarios with the proxy planner"""
        # Register booking scenario as per example in sprint_1.md
        self.proxy_planner.register_scenario(BookingScenario())
        # Add other scenarios here as they become available

    def _init_redis(self, config) -> redis.Redis:
        redis_config = config.get('redis', {})
        return redis.Redis(**redis_config)

    def process_command(self, command: str):
        logger.info(f"Processing command: {command}")
        self.view.display_message(f"Received command: {command}")
        self.view.start_progress()

        try:
            # Get appropriate scenario from proxy planner
            scenario, score = self.proxy_planner.classify_and_select(command)

            if score > 0:
                self.active_scenario = scenario
                # Execute the command with selected scenario
                self.active_scenario.execute(command)
            else:
                self.view.display_message(
                    "I'm not sure how to handle that command")

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.view.display_error(str(e))
        finally:
            self.view.stop_progress()

    def listen_for_messages(self):
        """Listen for messages from active scenarios"""
        # TODO: Implement Redis pub/sub listening
        pass

    def run(self):
        logger.info("Starting NLU Manager")
        self.view.display_message("Welcome to the Organization Agent")

        while True:
            try:
                command = self.view.get_input()
                if command.lower() in ['exit', 'quit']:
                    break
                self.process_command(command)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.view.display_error("An unexpected error occurred")

        self.view.display_message("Shutting down...")
        logger.info("NLU Manager stopped")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    manager = NLUManager(config=CONFIG)
    manager.run()
