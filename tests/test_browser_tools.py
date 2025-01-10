import pytest
from src.tools.browser.auth import LoginTool, BookingPageTool
from config import CONFIG
import logging

@pytest.mark.asyncio
class TestLoginTool:
    @pytest.fixture
    def login_tool(self):
        return LoginTool()

    async def test_successful_login(self, login_tool, mocker):
        # Get timeout from config
        timeout = CONFIG.isu_booking_creds.page_interaction_timeout

        # Mock page and its methods
        mock_page = mocker.AsyncMock()
        mock_page.url = "https://example.com/dashboard"
        mock_page.content.return_value = "Личный кабинет"
        mock_page.is_visible.return_value = True
        mock_page.evaluate.return_value = []
        
        # Mock click method separately to track its await
        mock_click = mocker.AsyncMock()
        mock_page.click = mock_click

        # Mock remaining page methods
        mock_page.goto = mocker.AsyncMock()
        mock_page.fill = mocker.AsyncMock()
        mock_page.wait_for_selector = mocker.AsyncMock()
        
        # Setup navigation context manager with proper async context handling
        navigation_context = mocker.AsyncMock()
        navigation_context.__aenter__ = mocker.AsyncMock()
        navigation_context.__aexit__ = mocker.AsyncMock()
        mock_page.expect_navigation = mocker.AsyncMock(return_value=navigation_context)

        # Mock browser manager
        mocker.patch.object(login_tool, '_get_page', return_value=mock_page)

        # Execute login
        result = await login_tool.execute(
            login_url="https://test.com",
            username="test",
            password="test123"
        )

        # Verify interactions
        mock_page.goto.assert_awaited_once_with("https://test.com", timeout=timeout)
        mock_page.wait_for_selector.assert_awaited_once_with('#username', timeout=timeout)
        mock_page.fill.assert_has_awaits([
            mocker.call('#username', 'test'),
            mocker.call('#password', 'test123')
        ])
        mock_page.expect_navigation.assert_called_once_with(timeout=timeout)


    async def test_failed_login(self, login_tool, mocker):
        # Mock page that raises exception
        mock_page = mocker.AsyncMock()
        mock_page.goto.side_effect = Exception("Connection failed")

        # Mock browser manager
        mocker.patch.object(login_tool, '_get_page', return_value=mock_page)

        result = await login_tool.execute()

        assert result['success'] is False
        assert 'error' in result
        assert "Connection failed" in result['error']

    async def test_verify_login_success(self, login_tool, mocker):
        mock_page = mocker.AsyncMock()
        mock_page.is_visible.return_value = True
        mock_page.content.return_value = "Личный кабинет"

        result = await login_tool._verify_login(mock_page)
        assert result is True

@pytest.mark.asyncio
class TestBookingPageTool:
    @pytest.fixture
    def booking_tool(self):
        return BookingPageTool()

    async def test_logged_in_status(self, booking_tool, mocker):
        mock_page = mocker.AsyncMock()
        mock_page.url = "https://example.com/booking"
        mock_page.content.return_value = "Бронирование помещений Мои заявки"

        mocker.patch.object(booking_tool, '_get_page', return_value=mock_page)

        result = await booking_tool.execute()

        assert result['status'] == 'logged_in'
        assert result['current_url'] == "https://example.com/booking"

    async def test_login_required_status(self, booking_tool, mocker):
        mock_page = mocker.AsyncMock()
        mock_page.url = "https://example.com/login"
        mock_page.content.return_value = "Войти с помощью"

        mocker.patch.object(booking_tool, '_get_page', return_value=mock_page)

        result = await booking_tool.execute()

        assert result['status'] == 'login_required'
        assert result['current_url'] == "https://example.com/login"

    async def test_unknown_status(self, booking_tool, mocker):
        mock_page = mocker.AsyncMock()
        mock_page.url = "https://example.com/unknown"
        mock_page.content.return_value = "Unexpected content"

        mocker.patch.object(booking_tool, '_get_page', return_value=mock_page)

        result = await booking_tool.execute()

        assert result['status'] == 'unknown'
        assert 'error' in result

    async def test_error_handling(self, booking_tool, mocker):
        mock_page = mocker.AsyncMock()
        mock_page.goto.side_effect = Exception("Network error")

        mocker.patch.object(booking_tool, '_get_page', return_value=mock_page)

        result = await booking_tool.execute()

        assert result['status'] == 'error'
        assert 'error' in result
        assert "Network error" in result['error']
