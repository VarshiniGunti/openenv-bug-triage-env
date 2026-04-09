"""Configuration management for the environment."""

import yaml
import os
import sys
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.config import Config


class ConfigManager:
    """Manages environment configuration from openenv.yaml file."""
    
    DEFAULT_CONFIG_PATH = "openenv.yaml"
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Config:
        """
        Load configuration from openenv.yaml file.
        
        Args:
            config_path: Path to configuration file (defaults to openenv.yaml)
            
        Returns:
            Config object with validated settings
            
        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration is invalid
        """
        if config_path is None:
            config_path = ConfigManager.DEFAULT_CONFIG_PATH
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            
            if config_dict is None:
                config_dict = {}
            
            # Validate and create Config object
            config = Config(**config_dict)
            return config
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    @staticmethod
    def get_default_config() -> Config:
        """
        Get default configuration.
        
        Returns:
            Config object with default values
        """
        return Config()
    
    @staticmethod
    def save_config(config: Config, config_path: Optional[str] = None) -> None:
        """
        Save configuration to openenv.yaml file.
        
        Args:
            config: Config object to save
            config_path: Path to save configuration file
        """
        if config_path is None:
            config_path = ConfigManager.DEFAULT_CONFIG_PATH
        
        config_dict = config.model_dump()
        
        # Create directory if needed
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
