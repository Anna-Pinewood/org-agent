import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)
project_path = Path(__file__).resolve().parents[1]


def load_config() -> dict:
    try:
        config_path = os.getenv('CONFIG_PATH', project_path / 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(
                f"Configuration loaded successfully from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


# Load config once when module is imported
config = load_config()
