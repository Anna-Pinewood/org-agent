import pytest
from unittest.mock import patch
from src.view import CLIView

class TestCLIView:
    def test_display_message(self, mock_console):
        console, output = mock_console
        view = CLIView()
        view.console = console
        
        view.display_message("Test message")
        assert "Test message" in output.getvalue()

    def test_display_error(self, mock_console):
        console, output = mock_console
        view = CLIView()
        view.console = console
        
        view.display_error("Test error")
        assert "Test error" in output.getvalue()
        assert "ERROR" in output.getvalue()

    @patch('src.view.Prompt.ask', return_value='test input')  # Fix patch path
    def test_get_input(self, mock_ask, mock_console):
        console, output = mock_console
        view = CLIView()
        view.console = console
        
        result = view.get_input("Test prompt")
        assert result == 'test input'
        mock_ask.assert_called_once()

    def test_progress_indicator(self, mock_console):
        console, output = mock_console
        view = CLIView()
        view.console = console
        
        view.start_progress("Testing")
        assert view.active_spinner is not None
        
        view.stop_progress()
        assert view.active_spinner is None

    def test_display_result(self, mock_console):
        console, output = mock_console
        view = CLIView()
        view.console = console
        
        view.display_result("Test result")
        output_text = output.getvalue()
        assert "Test result" in output_text
        assert "Result" in output_text
        assert "Complete" in output_text