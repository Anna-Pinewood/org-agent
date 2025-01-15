import logging
from src.config import CONFIG
from src.scenarios.base import ScenarioStep, StepStatus
from src.tools.base import ToolResponse
from src.tools.browser.click import CheckContentTool, ClickTool, FillTool, NavigateTool
from src.tools.browser.environment import BrowserEnvironment
from src.tools.call_human import CallHumanTool
logger = logging.getLogger(__name__)


class LoginStep(ScenarioStep):
    """Step for handling authentication to the booking system"""

    def __init__(self):
        super().__init__()
        self.status = StepStatus.NOT_STARTED
        self._success_texts = ["Личный кабинет", "Центр приложений"]
        self._register_tools()

    def _register_tools(self):
        self.toolbox.register_tool("NavigateTool", NavigateTool())
        self.toolbox.register_tool("CheckContentTool", CheckContentTool())
        self.toolbox.register_tool("FillTool", FillTool())
        self.toolbox.register_tool("ClickTool", ClickTool())
        self.toolbox.register_tool("CallHumanTool", CallHumanTool())

    async def execute(self, env: BrowserEnvironment) -> bool:
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
            msg = f"Navigating to login page: {CONFIG.isu_booking_creds.booking_login}"
            logger.info(msg)
            nav_result = await NavigateTool().execute(
                env=env,
                url=CONFIG.isu_booking_creds.booking_login
            )

            nav_check_result = await CheckContentTool().execute(
                env=env,
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
                environment=env,
                header_summary=msg
            )

            if not nav_check_result.success or not nav_result.success:
                logger.error(
                    "Failed to verify login page content: %s", nav_check_result.error)
                return False

            # Fill username
            msg = "Filling username field"
            logger.info(msg)
            username_result = await FillTool().execute(
                env=env,
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
                environment=env,
                header_summary=msg
            )
            if not username_result.success:
                logger.error("Failed to fill username: %s",
                             username_result.error)
                return False

            # Fill password
            msg = "Filling password field"
            logger.info(msg)
            password_result = await FillTool().execute(
                env=env,
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
                environment=env,
                header_summary=msg
            )
            if not password_result.success:
                logger.error("Failed to fill password: %s",
                             password_result.error)
                return False

            # Click login button
            msg = "Clicking login button – logging in with filled values"
            logger.info(msg)
            click_result = await ClickTool().execute(
                env=env,
                text="Вход"
            )
            await self._record_tool_execution(
                tool_name="ClickTool",
                params={"text": "Вход"},
                response=click_result,
                environment=env,
                # header_summary=msg
            )
            if not click_result.success:
                logger.error("Failed to click login button: %s",
                             click_result.error)
                return False

            # Verify successful login
            return await self.verify_success(environment=env)

        except Exception as e:
            logger.error("Login step failed with unexpected error: %s", str(e))
            self.status = StepStatus.FAILED
            return False

    async def verify_success(
            self,
            environment: BrowserEnvironment) -> bool:
        """
        Verify successful login by checking for expected page elements

        Args:
            browser_env: Browser environment instance

        Returns:
            bool: True if login successful, False otherwise
        """
        msg = "Verifying login success..."
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
            logger.info("Login successful - found expected page elements")
            self.status = StepStatus.COMPLETED
            return True

        logger.error(
            "Login verification failed - expected elements not found: %s",
            verify_result.error
        )
        self.status = StepStatus.FAILED
        return False
