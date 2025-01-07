
import pytest
from unittest.mock import patch, MagicMock
from src.llm_interface import LLMInterface
import litellm
import json

@pytest.fixture
def mock_litellm_response():
    return {
        'id': '2152975f594e46168ab5b307358a3ab0',
        'created': 1736246454,
        'model': 'mistral/mistral-large-latest',
        'object': 'chat.completion',
        'system_fingerprint': None,
        'choices': [{
            'finish_reason': 'stop',
            'index': 0,
            'message': {
                'content': 'I am a language model trained by the Mistral AI team.',
                'role': 'assistant',
                'tool_calls': None,
                'function_call': None
            }
        }],
        'usage': {
            'completion_tokens': 13,
            'prompt_tokens': 7,
            'total_tokens': 20,
            'completion_tokens_details': None,
            'prompt_tokens_details': None
        },
        'service_tier': None
    }

class TestLLMInterface:
    @pytest.fixture
    def llm(self):
        return LLMInterface(
            model_name="mistral/mistral-large-latest",
            llm_api_key="test_key",
            llm_base_url=None
        )

    @patch('litellm.completion')
    def test_send_request_basic(self, mock_completion, llm, mock_litellm_response):
        # Setup mock
        mock_completion.return_value = mock_litellm_response

        # Test basic request
        response = llm.send_request(prompt="Who are you?", call_params=None)
        
        # Verify the call
        mock_completion.assert_called_once_with(
            model="mistral/mistral-large-latest",
            messages=[{"role": "user", "content": "Who are you?"}],
            api_key="test_key",
            api_base=None
        )
        
        # Verify response
        assert response['id'] == '2152975f594e46168ab5b307358a3ab0'
        assert response['model'] == 'mistral/mistral-large-latest'
        assert response['choices'][0]['message']['content'] == 'I am a language model trained by the Mistral AI team.'

    @patch('litellm.completion')
    def test_send_request_with_params(self, mock_completion, llm, mock_litellm_response):
        mock_completion.return_value = mock_litellm_response
        
        # Test with format parameters
        prompt_template = "My name is {name}"
        params = {"name": "Alice"}
        response = llm.send_request(prompt=prompt_template, call_params=params)
        
        mock_completion.assert_called_once_with(
            model="mistral/mistral-large-latest",
            messages=[{"role": "user", "content": "My name is Alice"}],
            api_key="test_key",
            api_base=None
        )

    def test_get_response_content_json(self, llm, mock_litellm_response):
        # Test JSON response
        mock_litellm_response['choices'][0]['message']['content'] = '{"key": "value"}'
        result = llm.get_response_content(mock_litellm_response)
        assert isinstance(result, dict)
        assert result == {"key": "value"}

    def test_get_response_content_text(self, llm, mock_litellm_response):
        # Test text response
        result = llm.get_response_content(mock_litellm_response)
        assert isinstance(result, str)
        assert result == "I am a language model trained by the Mistral AI team."

    @patch('litellm.completion')
    def test_send_request_with_default_prompt(self, mock_completion, mock_litellm_response):
        llm = LLMInterface(
            model_name="mistral/mistral-large-latest",
            llm_api_key="test_key",
            llm_base_url=None,
            prompt="Default prompt"
        )
        mock_completion.return_value = mock_litellm_response
        
        response = llm.send_request()
        
        mock_completion.assert_called_once_with(
            model="mistral/mistral-large-latest",
            messages=[{"role": "user", "content": "Default prompt"}],
            api_key="test_key",
            api_base=None
        )