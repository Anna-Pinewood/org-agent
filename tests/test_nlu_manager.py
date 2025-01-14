import pytest
from unittest.mock import Mock, patch
from src.nlu_manager import NLUManager


@pytest.fixture(scope="function")  # Add scope
def nlu_manager(mock_config):
    return NLUManager(config=mock_config)


def test_nlu_manager_initialization(nlu_manager):
    assert nlu_manager.view is not None
    assert nlu_manager.config is not None
    assert nlu_manager.active_scenario is None


# Change patch target to where CLIView is imported
@patch('src.nlu_manager.CLIView')
def test_process_command(mock_view_class, nlu_manager):
    # Create mock view instance
    mock_view = Mock()
    mock_view_class.return_value = mock_view

    # Create new NLUManager instance with mocked view
    test_manager = NLUManager(config=nlu_manager.config)

    # Test the process_command
    test_manager.run_command_execution("test command")

    # Verify display_message was called
    mock_view.display_message.assert_called_once_with(
        "Received command: test command")


def test_command_exit(nlu_manager):
    with patch.object(nlu_manager.view, 'get_input', return_value='exit'):
        nlu_manager.run()
        # Should exit gracefully
