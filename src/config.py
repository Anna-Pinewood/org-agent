import logging
import os
from pathlib import Path
from omegaconf import OmegaConf

logger = logging.getLogger(__name__)
project_path = Path(__file__).resolve().parents[1]


def load_config():
    try:
        config_path = os.getenv('CONFIG_PATH', project_path / 'config.yaml')
        config = OmegaConf.load(config_path)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


# Load config once when module is imported
CONFIG = load_config()
