import pytest
import tempfile
import yaml
from rich.console import Console
import io

@pytest.fixture(scope="function")
def mock_config():
    return {
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'logging': {
            'level': 'INFO'
        }
    }

@pytest.fixture(scope="function")
def temp_config_file(mock_config):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as temp:
        yaml.dump(mock_config, temp)
        temp.flush()
        yield temp.name

@pytest.fixture(scope="function")
def mock_console():
    output = io.StringIO()
    console = Console(file=output, force_terminal=True)
    return console, output
