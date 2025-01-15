import logging
from src.config import CONFIG
from src.scenarios.base import ScenarioStep, StepStatus
from src.tools.browser.click import CheckContentTool, ClickTool, NavigateTool
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)


class NavigateToBookingStep(ScenarioStep):
    """Step for navigating to the booking creation page and verifying arrival"""

    def __init__(self):
        """Initialize step with required tools and success criteria"""
        super().__init__()
        self.status = StepStatus.NOT_STARTED
        self._success_texts = [
            "Карточка заявки",
            "Заявка",
            "Картотека заявок",
            "Проект заявки"
        ]
        self._register_tools()

    def _register_tools(self):
        """Register required tools for navigation and verification"""
        self.toolbox.register_tool("NavigateTool", NavigateTool())
        self.toolbox.register_tool("ClickTool", ClickTool())
        self.toolbox.register_tool("CheckContentTool", CheckContentTool())

    async def execute(self, env: BrowserEnvironment) -> bool:
        """
        Execute navigation sequence to booking page

        Args:
            browser_env: Browser environment instance

        Returns:
            bool: True if navigation successful, False otherwise
        """
        self.status = StepStatus.IN_PROGRESS
        logger.info("Starting navigation to booking page")

        try:
            # Navigate to booking page
            msg = f"Navigating to booking page: {CONFIG.isu_booking_creds.booking_url}"
            logger.info(msg)
            nav_result = await NavigateTool().execute(
                env=env,
                url=CONFIG.isu_booking_creds.booking_url
            )
            await self._record_tool_execution(
                tool_name="NavigateTool",
                params={"url": CONFIG.isu_booking_creds.booking_url},
                response=nav_result,
                environment=env,
                header_summary=msg
            )

            if not nav_result.success:
                logger.error(
                    "Failed to navigate to booking page: %s", nav_result.error)
                return False

            # Click "Create booking" button
            msg = "Clicking 'Create booking' button"
            logger.info(msg)
            click_result = await ClickTool().execute(
                env=env,
                text="Создать заявку"
            )
            await self._record_tool_execution(
                tool_name="ClickTool",
                params={"text": "Создать заявку"},
                response=click_result,
                environment=env,
                header_summary=msg
            )

            if not click_result.success:
                logger.error(
                    "Failed to click 'Create booking' button: %s", click_result.error)
                return False

            # Verify successful navigation
            return await self.verify_success(environment=env)

        except Exception as e:
            logger.error(
                "Navigation step failed with unexpected error: %s", str(e))
            self.status = StepStatus.FAILED
            return False

    async def verify_success(self, environment: BrowserEnvironment) -> bool:
        """
        Verify successful navigation by checking for expected page elements

        Args:
            environment: Browser environment instance

        Returns:
            bool: True if navigation successful, False otherwise
        """
        msg = "Verifying successful navigation to booking page"
        logger.info(msg)

        verify_result = await CheckContentTool().execute(
            env=environment,
            texts=self._success_texts
        )

        await self._record_tool_execution(
            tool_name="CheckContentTool",
            params={"texts": self._success_texts},
            response=verify_result,
            environment=environment,
            header_summary=msg
        )

        if verify_result.success:
            logger.info("Navigation successful - found expected page elements")
            self.status = StepStatus.COMPLETED
            return True

        logger.error(
            "Navigation verification failed - expected elements not found: %s",
            verify_result.error
        )
        self.status = StepStatus.FAILED
        return False

    @property
    def description(self) -> str:
        return "Navigates to the booking creation page and verifies successful arrival"
