"""
Tests for Cloud Storage Settings functionality.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, mock_open
from src.managers.cloud_storage_settings import CloudStorageSettings


class TestCloudStorageSettings:
    """Test cases for CloudStorageSettings."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.settings = None

    def teardown_method(self):
        """Cleanup test fixtures."""
        if self.settings:
            # Clean up test files
            import shutil
            if os.path.exists(self.settings.settings_dir):
                shutil.rmtree(self.settings.settings_dir)

    def create_test_settings(self):
        """Create CloudStorageSettings instance for testing."""
        with patch('src.managers.cloud_storage_settings.get_path_in_app') as mock_path:
            mock_path.return_value = self.temp_dir
            self.settings = CloudStorageSettings()
        return self.settings

    def test_initialization(self):
        """Test CloudStorageSettings initialization."""
        settings = self.create_test_settings()

        assert settings.settings_dir == self.temp_dir
        assert settings.config_file == os.path.join(self.temp_dir, "configurations.json")
        assert settings.key_file == os.path.join(self.temp_dir, ".encryption_key")
        assert os.path.exists(settings.settings_dir)
        assert os.path.exists(settings.key_file)

    def test_encryption_key_creation(self):
        """Test encryption key creation and retrieval."""
        settings = self.create_test_settings()

        # Key should be created
        assert os.path.exists(settings.key_file)
        assert len(settings._encryption_key) > 0

        # Key should be the same on subsequent loads
        key1 = settings._encryption_key
        settings2 = self.create_test_settings()
        key2 = settings2._encryption_key

        assert key1 == key2

    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        settings = self.create_test_settings()

        test_data = "sensitive password data"
        encrypted = settings._encrypt_data(test_data)
        decrypted = settings._decrypt_data(encrypted)

        assert encrypted != test_data  # Should be encrypted
        assert decrypted == test_data  # Should decrypt correctly

    def test_encrypt_decrypt_empty_data(self):
        """Test encryption/decryption of empty data."""
        settings = self.create_test_settings()

        test_data = ""
        encrypted = settings._encrypt_data(test_data)
        decrypted = settings._decrypt_data(encrypted)

        assert decrypted == test_data

    def test_save_webdav_configuration(self):
        """Test saving WebDAV configuration."""
        settings = self.create_test_settings()

        config = {
            'type': 'webdav',
            'url': 'https://example.com/webdav/',
            'username': 'testuser',
            'password': 'testpass',
            'auth_type': 'basic',
            'remote_directory': 'ArchImmich'
        }

        result = settings.save_configuration("test_webdav", config)

        assert result is True
        assert os.path.exists(settings.config_file)

        # Verify configuration was saved
        with open(settings.config_file, 'r') as f:
            saved_configs = json.load(f)

        assert "test_webdav" in saved_configs
        saved_config = saved_configs["test_webdav"]

        # Password should be encrypted
        assert saved_config['password'] != 'testpass'
        assert saved_config['type'] == 'webdav'
        assert saved_config['url'] == 'https://example.com/webdav/'
        assert saved_config['username'] == 'testuser'

        # Should have metadata
        assert '_metadata' in saved_config
        assert saved_config['_metadata']['name'] == "test_webdav"

    def test_save_s3_configuration(self):
        """Test saving S3 configuration."""
        settings = self.create_test_settings()

        config = {
            'type': 's3',
            'endpoint_url': 'https://s3.amazonaws.com',
            'access_key': 'test_access_key',
            'secret_key': 'test_secret_key',
            'bucket_name': 'test_bucket',
            'region': 'us-east-1',
            'remote_prefix': 'ArchImmich/'
        }

        result = settings.save_configuration("test_s3", config)

        assert result is True

        # Verify configuration was saved
        with open(settings.config_file, 'r') as f:
            saved_configs = json.load(f)

        assert "test_s3" in saved_configs
        saved_config = saved_configs["test_s3"]

        # Secret key should be encrypted
        assert saved_config['secret_key'] != 'test_secret_key'
        assert saved_config['type'] == 's3'
        assert saved_config['endpoint_url'] == 'https://s3.amazonaws.com'
        assert saved_config['access_key'] == 'test_access_key'

    def test_load_webdav_configuration(self):
        """Test loading WebDAV configuration."""
        settings = self.create_test_settings()

        # Save configuration first
        config = {
            'type': 'webdav',
            'url': 'https://example.com/webdav/',
            'username': 'testuser',
            'password': 'testpass',
            'auth_type': 'basic'
        }
        settings.save_configuration("test_webdav", config)

        # Load configuration
        loaded_config = settings.load_configuration("test_webdav")

        assert loaded_config is not None
        assert loaded_config['type'] == 'webdav'
        assert loaded_config['url'] == 'https://example.com/webdav/'
        assert loaded_config['username'] == 'testuser'
        assert loaded_config['password'] == 'testpass'  # Should be decrypted
        assert loaded_config['auth_type'] == 'basic'

        # Metadata should be removed
        assert '_metadata' not in loaded_config

    def test_load_nonexistent_configuration(self):
        """Test loading non-existent configuration."""
        settings = self.create_test_settings()

        loaded_config = settings.load_configuration("nonexistent")

        assert loaded_config is None

    def test_load_all_configurations(self):
        """Test loading all configurations."""
        settings = self.create_test_settings()

        # Save multiple configurations
        config1 = {'type': 'webdav', 'url': 'https://example1.com', 'username': 'user1', 'password': 'pass1'}
        config2 = {'type': 's3', 'endpoint_url': 'https://s3.amazonaws.com', 'access_key': 'key1', 'secret_key': 'secret1', 'bucket_name': 'bucket1'}

        settings.save_configuration("config1", config1)
        settings.save_configuration("config2", config2)

        all_configs = settings.load_all_configurations()

        assert len(all_configs) == 2
        assert "config1" in all_configs
        assert "config2" in all_configs

    def test_delete_configuration(self):
        """Test deleting configuration."""
        settings = self.create_test_settings()

        # Save configuration
        config = {'type': 'webdav', 'url': 'https://example.com', 'username': 'user', 'password': 'pass'}
        settings.save_configuration("test_config", config)

        # Verify it exists
        assert settings.load_configuration("test_config") is not None

        # Delete configuration
        result = settings.delete_configuration("test_config")

        assert result is True
        assert settings.load_configuration("test_config") is None

    def test_delete_nonexistent_configuration(self):
        """Test deleting non-existent configuration."""
        settings = self.create_test_settings()

        result = settings.delete_configuration("nonexistent")

        assert result is False

    def test_list_configurations(self):
        """Test listing configurations with metadata."""
        settings = self.create_test_settings()

        # Save configurations
        config1 = {'type': 'webdav', 'url': 'https://example1.com', 'username': 'user1', 'password': 'pass1'}
        config2 = {'type': 's3', 'endpoint_url': 'https://s3.amazonaws.com', 'access_key': 'key1', 'secret_key': 'secret1', 'bucket_name': 'bucket1'}

        settings.save_configuration("webdav_config", config1)
        settings.save_configuration("s3_config", config2)

        configs_list = settings.list_configurations()

        assert len(configs_list) == 2

        # Find configurations
        webdav_config = next(c for c in configs_list if c['name'] == 'webdav_config')
        s3_config = next(c for c in configs_list if c['name'] == 's3_config')

        assert webdav_config['type'] == 'webdav'
        assert s3_config['type'] == 's3'
        assert 'created_at' in webdav_config
        assert 'updated_at' in webdav_config
        assert 'display_name' in webdav_config

    def test_get_display_name_webdav(self):
        """Test display name generation for WebDAV."""
        settings = self.create_test_settings()

        config = {
            'type': 'webdav',
            'url': 'https://example.com/webdav/',
            'username': 'testuser'
        }

        display_name = settings._get_display_name(config)

        assert 'WebDAV' in display_name
        assert 'testuser' in display_name
        assert 'example.com' in display_name

    def test_get_display_name_s3(self):
        """Test display name generation for S3."""
        settings = self.create_test_settings()

        config = {
            'type': 's3',
            'endpoint_url': 'https://s3.amazonaws.com',
            'bucket_name': 'test-bucket'
        }

        display_name = settings._get_display_name(config)

        assert 'S3' in display_name
        assert 'test-bucket' in display_name
        assert 's3.amazonaws.com' in display_name

    def test_update_configuration(self):
        """Test updating existing configuration."""
        settings = self.create_test_settings()

        # Save initial configuration
        initial_config = {
            'type': 'webdav',
            'url': 'https://example.com/webdav/',
            'username': 'testuser',
            'password': 'oldpass'
        }
        settings.save_configuration("test_config", initial_config)

        # Update configuration
        updated_config = {
            'type': 'webdav',
            'url': 'https://example.com/webdav/',
            'username': 'testuser',
            'password': 'newpass'
        }

        result = settings.update_configuration("test_config", updated_config)

        assert result is True

        # Verify update
        loaded_config = settings.load_configuration("test_config")
        assert loaded_config['password'] == 'newpass'

    def test_update_nonexistent_configuration(self):
        """Test updating non-existent configuration."""
        settings = self.create_test_settings()

        config = {'type': 'webdav', 'url': 'https://example.com', 'username': 'user', 'password': 'pass'}

        result = settings.update_configuration("nonexistent", config)

        assert result is False

    def test_clear_all_configurations(self):
        """Test clearing all configurations."""
        settings = self.create_test_settings()

        # Save some configurations
        config1 = {'type': 'webdav', 'url': 'https://example1.com', 'username': 'user1', 'password': 'pass1'}
        config2 = {'type': 's3', 'endpoint_url': 'https://s3.amazonaws.com', 'access_key': 'key1', 'secret_key': 'secret1', 'bucket_name': 'bucket1'}

        settings.save_configuration("config1", config1)
        settings.save_configuration("config2", config2)

        # Verify they exist
        assert len(settings.load_all_configurations()) == 2

        # Clear all
        result = settings.clear_all_configurations()

        assert result is True
        assert not os.path.exists(settings.config_file)
        assert len(settings.load_all_configurations()) == 0

    def test_encryption_key_file_permissions(self):
        """Test that encryption key file has restrictive permissions."""
        settings = self.create_test_settings()

        # Check file permissions (this might not work on all systems)
        if hasattr(os, 'stat'):
            stat_info = os.stat(settings.key_file)
            # On Unix systems, check that file is not readable by others
            if hasattr(stat_info, 'st_mode'):
                # File should not be readable by group or others
                assert not (stat_info.st_mode & 0o044)

    def test_error_handling_save_configuration(self):
        """Test error handling in save_configuration."""
        settings = self.create_test_settings()

        # Mock file write to raise an exception
        with patch('builtins.open', side_effect=IOError("Write error")):
            result = settings.save_configuration("test", {'type': 'webdav'})
            assert result is False

    def test_error_handling_load_configuration(self):
        """Test error handling in load_configuration."""
        settings = self.create_test_settings()

        # Mock file read to raise an exception
        with patch('builtins.open', side_effect=IOError("Read error")):
            result = settings.load_configuration("test")
            assert result is None

    def test_corrupted_encrypted_data(self):
        """Test handling of corrupted encrypted data."""
        settings = self.create_test_settings()

        # Test decryption of corrupted data
        result = settings._decrypt_data("corrupted_encrypted_data")
        assert result == ""  # Should return empty string on error
