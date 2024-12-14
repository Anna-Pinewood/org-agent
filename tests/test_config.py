import pytest
import os
from omegaconf import OmegaConf
from src.config import load_config

def test_config_loading(temp_config_file):
    os.environ['CONFIG_PATH'] = temp_config_file
    config = load_config()
    assert 'redis' in config
    assert config.redis.host == 'localhost'

def test_config_loading_file_not_found():
    os.environ['CONFIG_PATH'] = 'nonexistent.yaml'
    with pytest.raises(FileNotFoundError):
        load_config()

def test_config_loading_invalid_yaml(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text(": invalid: yaml: content")
    os.environ['CONFIG_PATH'] = str(invalid_yaml)
    with pytest.raises(Exception):
        load_config()
