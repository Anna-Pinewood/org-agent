import pytest
import requests
from unittest.mock import Mock, patch
from src.llm_interface import LLMInterface, RunPodInterface

@pytest.fixture
def runpod_interface():
    return RunPodInterface(
        base_url="https://api.runpod.ai/v2/llama2-70b-4bit",
        api_key="test_api_key"
    )

@pytest.fixture
def mock_successful_response():
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "COMPLETED",
        "output": [{
            "choices": [{
                "text": "test response"
            }]
        }],
        "input": {
            "prompt": "test prompt"
        }
    }
    mock_response.raise_for_status.return_value = None
    return mock_response

@pytest.fixture
def mock_health_response():
    mock_response = Mock()
    mock_response.json.return_value = {"status": "healthy"}
    mock_response.raise_for_status.return_value = None
    return mock_response

def test_llm_interface_is_abstract():
    with pytest.raises(TypeError):
        LLMInterface()

def test_runpod_interface_initialization():
    interface = RunPodInterface(
        base_url="https://api.runpod.ai/v2/llama2-70b-4bit",
        api_key="test_key"
    )
    assert interface.endpoint_url == "https://api.runpod.ai/v2/llama2-70b-4bit/run"
    assert interface.headers["Authorization"] == "Bearer test_key"

@patch('requests.get')
def test_get_health_status_success(mock_get, runpod_interface, mock_health_response):
    mock_get.return_value = mock_health_response
    status = runpod_interface.get_health_status()
    assert status == {"status": "healthy"}
    mock_get.assert_called_once()

@patch('requests.get')
def test_get_health_status_failure(mock_get, runpod_interface):
    mock_get.side_effect = requests.RequestException("Connection failed")
    with pytest.raises(ConnectionError):
        runpod_interface.get_health_status()

@patch('requests.post')
def test_send_request_success(mock_post, runpod_interface, mock_successful_response):
    mock_post.return_value = mock_successful_response
    response = runpod_interface.send_request("test prompt")
    assert response == {
        "output": "test response",
        "prompt": "test prompt"
    }
    mock_post.assert_called_once()

@patch('requests.post')
def test_send_request_timeout(mock_post, runpod_interface):
    mock_post.side_effect = requests.Timeout("Request timed out")
    with pytest.raises(ConnectionError) as exc_info:
        runpod_interface.send_request("test prompt")
    assert "timed out" in str(exc_info.value)

@patch('requests.post')
@patch('requests.get')
def test_send_request_queued(mock_get, mock_post, runpod_interface):
    queued_response = Mock()
    queued_response.json.return_value = {
        "status": "IN_QUEUE",
        "id": "test_id"
    }
    queued_response.raise_for_status.return_value = None
    
    completed_response = Mock()
    completed_response.json.return_value = {
        "status": "COMPLETED",
        "output": [{
            "choices": [{
                "text": "test response"
            }]
        }],
        "input": {
            "prompt": "test prompt"
        }
    }
    completed_response.raise_for_status.return_value = None
    
    mock_post.return_value = queued_response
    mock_get.return_value = completed_response
    
    response = runpod_interface.send_request("test prompt")
    assert response["output"] == "test response"
    mock_post.assert_called_once()
    mock_get.assert_called_once()
