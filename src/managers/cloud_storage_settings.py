"""
Cloud Storage Settings Manager for ArchImmich
Handles secure storage and retrieval of cloud storage configurations.
"""

import json
import os
import base64
import hashlib
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from src.utils.helpers import get_path_in_app


class CloudStorageSettings:
    """
    Manages cloud storage configurations with encryption.
    Provides secure storage of credentials and configuration data.
    """

    def __init__(self):
        self.settings_dir = get_path_in_app("cloud_storage")
        self.config_file = os.path.join(self.settings_dir, "configurations.json")
        self.key_file = os.path.join(self.settings_dir, ".encryption_key")
        self._ensure_directories()
        self._encryption_key = self._get_or_create_encryption_key()

    def _ensure_directories(self):
        """Ensure the settings directory exists."""
        os.makedirs(self.settings_dir, exist_ok=True)

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure storage."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        fernet = Fernet(self._encryption_key)
        encrypted_data = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            fernet = Fernet(self._encryption_key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # If decryption fails, return empty string
            return ""

    def save_configuration(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Save a cloud storage configuration.

        Args:
            name: Configuration name
            config: Configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing configurations
            configurations = self.load_all_configurations()

            # Encrypt sensitive fields
            encrypted_config = config.copy()
            if config.get('type') == 'webdav':
                encrypted_config['password'] = self._encrypt_data(config.get('password', ''))
            elif config.get('type') == 's3':
                encrypted_config['secret_key'] = self._encrypt_data(config.get('secret_key', ''))

            # Add metadata
            encrypted_config['_metadata'] = {
                'name': name,
                'created_at': self._get_timestamp(),
                'updated_at': self._get_timestamp()
            }

            # Save configuration
            configurations[name] = encrypted_config

            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(configurations, f, indent=2)

            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)

            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def load_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific cloud storage configuration.

        Args:
            name: Configuration name

        Returns:
            Configuration dictionary or None if not found
        """
        try:
            configurations = self.load_all_configurations()
            if name not in configurations:
                return None

            config = configurations[name].copy()

            # Decrypt sensitive fields
            if config.get('type') == 'webdav':
                config['password'] = self._decrypt_data(config.get('password', ''))
            elif config.get('type') == 's3':
                config['secret_key'] = self._decrypt_data(config.get('secret_key', ''))

            # Remove metadata
            config.pop('_metadata', None)

            return config

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None

    def load_all_configurations(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all cloud storage configurations.

        Returns:
            Dictionary of all configurations
        """
        try:
            if not os.path.exists(self.config_file):
                return {}

            with open(self.config_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading configurations: {e}")
            return {}

    def delete_configuration(self, name: str) -> bool:
        """
        Delete a cloud storage configuration.

        Args:
            name: Configuration name

        Returns:
            True if successful, False otherwise
        """
        try:
            configurations = self.load_all_configurations()
            if name not in configurations:
                return False

            del configurations[name]

            # Write updated configurations
            with open(self.config_file, 'w') as f:
                json.dump(configurations, f, indent=2)

            return True

        except Exception as e:
            print(f"Error deleting configuration: {e}")
            return False

    def list_configurations(self) -> List[Dict[str, Any]]:
        """
        List all available configurations with metadata.

        Returns:
            List of configuration metadata
        """
        try:
            configurations = self.load_all_configurations()
            result = []

            for name, config in configurations.items():
                metadata = config.get('_metadata', {})
                result.append({
                    'name': name,
                    'type': config.get('type', 'unknown'),
                    'created_at': metadata.get('created_at', ''),
                    'updated_at': metadata.get('updated_at', ''),
                    'display_name': self._get_display_name(config)
                })

            return result

        except Exception as e:
            print(f"Error listing configurations: {e}")
            return []

    def _get_display_name(self, config: Dict[str, Any]) -> str:
        """Get a display name for the configuration."""
        # First, check if user provided a custom display name
        custom_name = config.get('display_name', '').strip()
        if custom_name:
            return custom_name

        # Fallback to auto-generated name if no custom name provided
        if config.get('type') == 'webdav':
            url = config.get('url', '')
            username = config.get('username', '')
            if url and username:
                # Extract domain from URL
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    return f"WebDAV ({username}@{domain})"
                except:
                    return f"WebDAV ({username})"
            return "WebDAV Configuration"

        elif config.get('type') == 's3':
            endpoint = config.get('endpoint_url', '')
            bucket = config.get('bucket_name', '')
            if endpoint and bucket:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(endpoint).netloc
                    return f"S3 ({bucket}@{domain})"
                except:
                    return f"S3 ({bucket})"
            return "S3 Configuration"

        return "Unknown Configuration"

    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def update_configuration(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Update an existing configuration.

        Args:
            name: Configuration name
            config: Updated configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            configurations = self.load_all_configurations()
            if name not in configurations:
                return False

            # Preserve metadata
            old_metadata = configurations[name].get('_metadata', {})

            # Encrypt sensitive fields
            encrypted_config = config.copy()
            if config.get('type') == 'webdav':
                encrypted_config['password'] = self._encrypt_data(config.get('password', ''))
            elif config.get('type') == 's3':
                encrypted_config['secret_key'] = self._encrypt_data(config.get('secret_key', ''))

            # Update metadata
            encrypted_config['_metadata'] = {
                'name': name,
                'created_at': old_metadata.get('created_at', self._get_timestamp()),
                'updated_at': self._get_timestamp()
            }

            # Update configuration
            configurations[name] = encrypted_config

            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(configurations, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating configuration: {e}")
            return False

    def clear_all_configurations(self) -> bool:
        """
        Clear all stored configurations.

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            return True
        except Exception as e:
            print(f"Error clearing configurations: {e}")
            return False
