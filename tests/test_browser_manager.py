import pytest
from src.tools.browser.manager import BrowserManager
import logging

@pytest.mark.asyncio
async def test_browser_startup_logging(caplog):
    caplog.set_level(logging.DEBUG)
    manager = BrowserManager()
    
    await manager.ensure_browser()
    assert "Starting new browser instance" in caplog.text
    
    await manager.close()

@pytest.mark.asyncio
async def test_browser_console_logging(caplog):
    caplog.set_level(logging.DEBUG)
    manager = BrowserManager()
    
    await manager.ensure_browser()
    page = await manager.get_page()
    
    # Simulate console message from browser
    await page.evaluate("console.log('test message')")
    
    assert "Browser console: test message" in caplog.text
    
    await manager.close()

@pytest.mark.asyncio
async def test_browser_cleanup(caplog):
    manager = BrowserManager()
    await manager.ensure_browser()
    
    assert manager._browser is not None
    assert manager._context is not None
    assert manager._page is not None
    
    await manager.close()
    
    assert manager._browser is None
    assert manager._context is None
    assert manager._page is None
