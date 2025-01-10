import logging
import asyncio
from typing import Optional
import redis
from planner import ProxyPlanner
from scenarios.booking import BookingScenario
from view import CLIView
from config import CONFIG

logger = logging.getLogger(__name__)


class NLUManager:
    """
    Natural Language Understanding Manager that coordinates processing of user commands
    and manages scenarios execution
    """
    def __init__(self, config):
        """
        Initialize NLU Manager with configuration and required components
        
        Args:
            config: Application configuration object
        """
        self.view = CLIView()
        self.config = config
        self.proxy_planner = ProxyPlanner()
        self._register_scenarios()
        self.active_scenario = None

    def _register_scenarios(self) -> None:
        """Register all available scenarios with the proxy planner"""
        logger.debug("Registering scenarios")
        self.proxy_planner.register_scenario(BookingScenario())
        # Add other scenarios here as they become available

    def _init_redis(self, config) -> redis.Redis:
        """
        Initialize Redis connection
        
        Args:
            config: Redis configuration dictionary
            
        Returns:
            redis.Redis: Configured Redis client
        """
        redis_config = config.get('redis', {})
        return redis.Redis(**redis_config)

    async def process_command(self, command: str) -> None:
        """
        Process a user command by selecting and executing appropriate scenario
        
        Args:
            command: User's natural language command
        """
        logger.info("Processing command: %s", command)
        self.view.display_message(f"Received command: {command}")
        self.view.start_progress()

        try:
            # Get appropriate scenario from proxy planner
            scenario, score = self.proxy_planner.classify_and_select(command)

            if score > 0:
                self.active_scenario = scenario
                # Execute the command with selected scenario - now properly awaited
                await self.active_scenario.execute(command)
            else:
                self.view.display_message(
                    "I'm not sure how to handle that command")

        except Exception as e:
            logger.error("Error processing command: %s", str(e))
            self.view.display_error(str(e))
        finally:
            self.view.stop_progress()

    async def run(self) -> None:
        """Main loop that processes user input until exit command is received"""
        logger.info("Starting NLU Manager")
        self.view.display_message("Welcome to the Organization Agent")

        while True:
            try:
                command = self.view.get_input()
                if command.lower() in ['exit', 'quit']:
                    break
                await self.process_command(command)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error("Unexpected error: %s", str(e))
                self.view.display_error("An unexpected error occurred")

        self.view.display_message("Shutting down...")
        logger.info("NLU Manager stopped")


def main():
    """Entry point for the application"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    manager = NLUManager(config=CONFIG)
    asyncio.run(manager.run())


if __name__ == "__main__":
    main()