import logging
from src.config import CONFIG
from src.scenarios.base import ScenarioStep, StepStatus
from src.tools.base import ToolResponse
from src.tools.browser.click import CheckContentTool, ClickTool, FillTool, NavigateTool
from src.tools.browser.environment import BrowserEnvironment
logger = logging.getLogger(__name__)


class LoginStep(ScenarioStep):
    """Step for handling authentication to the booking system"""
    def __init__(self):
        super().__init__()
        self.status = StepStatus.NOT_STARTED
        self._success_texts = ["Личный кабинет", "Центр приложений"]

    async def execute(self, browser_env: BrowserEnvironment) -> bool:
        """
        Execute login sequence with full logging and history tracking

        Args:
            browser_env: Browser environment instance

        Returns:
            bool: True if login successful, False otherwise
        """
        self.status = StepStatus.IN_PROGRESS
        logger.info("Starting login step execution")

        try:
            # Navigate to login page
            logger.info("Navigating to login page: %s",
                        CONFIG.isu_booking_creds.booking_login)
            nav_result = await NavigateTool().execute(
                env=browser_env,
                url=CONFIG.isu_booking_creds.booking_login
            )

            nav_check_result = await CheckContentTool().execute(
                env=browser_env,
                texts=["Имя пользователя или E-mail"]
            )

            await self._record_tool_execution(
                tool_name="NavigateTool",
                params={"url": CONFIG.isu_booking_creds.booking_login},
                response=ToolResponse(
                    success=nav_check_result.success,
                    meta={"action": "navigate",
                          "url": CONFIG.isu_booking_creds.booking_login}
                ),
                browser_env=browser_env
            )

            if not nav_check_result.success or not nav_result.success:
                logger.error(
                    "Failed to verify login page content: %s", nav_check_result.error)
                return False

            # Fill username
            logger.info("Filling username field")
            username_result = await FillTool().execute(
                env=browser_env,
                selector="#username",
                value=CONFIG.isu_booking_creds.username
            )
            await self._record_tool_execution(
                tool_name="FillTool",
                params={
                    "selector": "#username",
                    "value": "[REDACTED]"
                },
                response=username_result,
                browser_env=browser_env
            )
            if not username_result.success:
                logger.error("Failed to fill username: %s",
                             username_result.error)
                return False

            # Fill password
            logger.info("Filling password field")
            password_result = await FillTool().execute(
                env=browser_env,
                selector="#password",
                value=CONFIG.isu_booking_creds.password
            )
            await self._record_tool_execution(
                tool_name="FillTool",
                params={
                    "selector": "#password",
                    "value": "[REDACTED]"
                },
                response=password_result,
                browser_env=browser_env
            )
            if not password_result.success:
                logger.error("Failed to fill password: %s",
                             password_result.error)
                return False

            # Click login button
            logger.info("Clicking login button")
            click_result = await ClickTool().execute(
                env=browser_env,
                text="Вход"
            )
            await self._record_tool_execution(
                tool_name="ClickTool",
                params={"text": "Вход"},
                response=click_result,
                browser_env=browser_env
            )
            if not click_result.success:
                logger.error("Failed to click login button: %s",
                             click_result.error)
                return False

            # Verify successful login
            return await self.verify_success(browser_env)

        except Exception as e:
            logger.error("Login step failed with unexpected error: %s", str(e))
            self.status = StepStatus.FAILED
            return False

    async def verify_success(self, browser_env: BrowserEnvironment) -> bool:
        """
        Verify successful login by checking for expected page elements

        Args:
            browser_env: Browser environment instance

        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info("Verifying login success")

        verify_result = await CheckContentTool().execute(
            env=browser_env,
            texts=self._success_texts
        )

        if verify_result.success:
            logger.info("Login successful - found expected page elements")
            self.status = StepStatus.COMPLETED
            return True

        logger.error(
            "Login verification failed - expected elements not found: %s",
            verify_result.error
        )
        self.status = StepStatus.FAILED
        return False
