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

@patch('src.view.CLIView')  # Fix patch path from org_agent.src.view.CLIView
def test_process_command(mock_view, nlu_manager):
    nlu_manager.process_command("test command")
    mock_view.assert_called()

def test_command_exit(nlu_manager):
    with patch.object(nlu_manager.view, 'get_input', return_value='exit'):
        nlu_manager.run()
        # Should exit gracefully