"""
Tests for download resume functionality in ArchImmich.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, mock_open, call
from PyQt5.QtWidgets import QApplication, QProgressBar

from src.managers.export_manager import ExportManager
from src.ui.components.export_component import ExportComponent
from src.managers.login_manager import LoginManager


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_api_manager():
    """Create a mock API manager."""
    mock_api = MagicMock()
    mock_api.debug = {'verbose_logging': False}
    mock_api.server_url = "http://test-server.com"  # Add server_url for new Range header logic
    return mock_api


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return MagicMock()


@pytest.fixture
def export_manager(mock_api_manager, mock_logger, temp_output_dir):
    """Create an ExportManager instance for testing."""
    stop_flag = MagicMock(return_value=False)
    return ExportManager(mock_api_manager, mock_logger, temp_output_dir, stop_flag)


@pytest.fixture
def export_component():
    """Create an ExportComponent for testing."""
    import sys
    from PyQt5.QtTest import QTest

    # Skip Qt-dependent tests in headless environment
    if 'pytest' in sys.modules and not QApplication.instance():
        try:
            app = QApplication([])
        except Exception:
            pytest.skip("Qt GUI not available")

    login_manager = MagicMock(spec=LoginManager)

    # Mock the setup_ui method to avoid Qt widget creation
    with patch.object(ExportComponent, 'setup_ui'):
        component = ExportComponent(login_manager)
        component.output_dir = "/tmp/test"
        # Initialize attributes that would normally be created in setup_ui
        component.stop_button = MagicMock()
        component.resume_button = MagicMock()
        component.export_button = MagicMock()
        component.output_dir_button = MagicMock()
        return component


class TestResumeMetadata:
    """Test resume metadata management."""

    def test_save_resume_metadata(self, export_manager):
        """Test saving resume metadata."""
        asset_ids = ["id1", "id2"]
        total_size = 1000000
        downloaded_size = 500000
        archive_name = "test_archive"

        result = export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        assert result is True
        metadata_path = export_manager.get_resume_metadata_path(archive_name)
        assert os.path.exists(metadata_path)

        # Verify metadata content
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        assert metadata['archive_name'] == archive_name
        assert metadata['asset_ids'] == asset_ids
        assert metadata['total_size'] == total_size
        assert metadata['downloaded_size'] == downloaded_size
        assert 'timestamp' in metadata
        assert 'partial_file_path' in metadata

    def test_load_resume_metadata_success(self, export_manager, temp_output_dir):
        """Test loading resume metadata successfully."""
        archive_name = "test_archive"
        asset_ids = ["id1", "id2"]
        total_size = 1000000
        downloaded_size = 500000

        # Create partial file
        partial_file_path = os.path.join(temp_output_dir, f"{archive_name}.zip.partial")
        with open(partial_file_path, 'wb') as f:
            f.write(b"partial data")

        # Save metadata first
        export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        # Load metadata
        metadata = export_manager.load_resume_metadata(archive_name)

        assert metadata is not None
        assert metadata['archive_name'] == archive_name
        assert metadata['asset_ids'] == asset_ids
        assert metadata['total_size'] == total_size
        assert metadata['downloaded_size'] == downloaded_size

    def test_load_resume_metadata_missing_partial_file(self, export_manager):
        """Test loading resume metadata when partial file is missing."""
        archive_name = "test_archive"
        asset_ids = ["id1", "id2"]
        total_size = 1000000
        downloaded_size = 500000

        # Save metadata without creating partial file
        export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        # Load metadata - should clean up and return None
        metadata = export_manager.load_resume_metadata(archive_name)

        assert metadata is None
        # Metadata file should be cleaned up
        metadata_path = export_manager.get_resume_metadata_path(archive_name)
        assert not os.path.exists(metadata_path)

    def test_can_resume_download_success(self, export_manager, temp_output_dir):
        """Test successful resume capability check."""
        archive_name = "test_archive"
        asset_ids = ["id1", "id2"]
        total_size = 1000000
        downloaded_size = 500000

        # Create partial file
        partial_file_path = os.path.join(temp_output_dir, f"{archive_name}.zip.partial")
        with open(partial_file_path, 'wb') as f:
            f.write(b"partial data")

        # Save metadata
        export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        can_resume, existing_bytes = export_manager.can_resume_download(
            archive_name, asset_ids, total_size
        )

        assert can_resume is True
        assert existing_bytes == downloaded_size

    def test_can_resume_download_mismatch(self, export_manager, temp_output_dir):
        """Test resume capability check with parameter mismatch."""
        archive_name = "test_archive"
        asset_ids = ["id1", "id2"]
        different_asset_ids = ["id3", "id4"]
        total_size = 1000000
        downloaded_size = 500000

        # Create partial file
        partial_file_path = os.path.join(temp_output_dir, f"{archive_name}.zip.partial")
        with open(partial_file_path, 'wb') as f:
            f.write(b"partial data")

        # Save metadata with original asset IDs
        export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        # Try to resume with different asset IDs
        can_resume, existing_bytes = export_manager.can_resume_download(
            archive_name, different_asset_ids, total_size
        )

        assert can_resume is False
        assert existing_bytes == 0


class TestDownloadResume:
    """Test download resume functionality."""

    @patch('requests.Response')
    def test_download_archive_fresh_start(self, mock_response, export_manager):
        """Test download archive starting fresh."""
        mock_response.ok = True
        mock_response.iter_content = MagicMock(return_value=[b"chunk1", b"chunk2"])
        mock_response.headers = {}  # No special headers for fresh download
        export_manager.api_manager.post.return_value = mock_response

        mock_progress_bar = MagicMock(spec=QProgressBar)

        with patch('builtins.open', mock_open()), \
             patch('os.path.exists', return_value=False), \
             patch('os.makedirs'), \
             patch('os.rename'), \
             patch('os.path.getsize', return_value=12):  # Mock final file size

            result = export_manager.download_archive(
                ["id1", "id2"], "test_archive", 2048, mock_progress_bar
            )

            assert result == "completed"
            export_manager.api_manager.post.assert_called_once()

    @patch('requests.Response')
    def test_download_archive_resume(self, mock_response, export_manager, temp_output_dir):
        """Test download archive with resume."""
        # Setup existing partial download
        archive_name = "test_archive"
        asset_ids = ["id1", "id2"]
        total_size = 2048
        downloaded_size = 1024

        # Create partial file
        partial_file_path = os.path.join(temp_output_dir, f"{archive_name}.zip.partial")
        with open(partial_file_path, 'wb') as f:
            f.write(b"x" * downloaded_size)

        # Save metadata
        export_manager.save_resume_metadata(
            archive_name, asset_ids, total_size, downloaded_size
        )

        # Mock response for resume - server honors Range request
        mock_response.ok = True
        mock_response.iter_content = MagicMock(return_value=[b"chunk3", b"chunk4"])
        mock_response.headers = {
            'Content-Range': f'bytes {downloaded_size}-{total_size-1}/{total_size}',
            'Content-Length': str(total_size - downloaded_size)
        }
        export_manager.api_manager.post.return_value = mock_response

        mock_progress_bar = MagicMock(spec=QProgressBar)

        with patch('os.makedirs'), \
             patch('os.rename'), \
             patch('os.path.getsize', return_value=total_size):  # Mock final file size

            result = export_manager.download_archive(
                asset_ids, archive_name, total_size, mock_progress_bar
            )

            assert result == "completed"
            # Should be called with Range header
            call_args = export_manager.api_manager.post.call_args
            assert 'headers' in call_args.kwargs
            assert call_args.kwargs['headers']['Range'] == f"bytes={downloaded_size}-"

    def test_download_archive_pause(self, export_manager):
        """Test download archive pause functionality."""
        # Mock stop flag to return True after first chunk
        call_count = 0
        def mock_stop_flag():
            nonlocal call_count
            call_count += 1
            return call_count > 1

        export_manager.stop_flag = mock_stop_flag

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_content = MagicMock(return_value=[b"chunk1", b"chunk2", b"chunk3"])
        export_manager.api_manager.post.return_value = mock_response

        mock_progress_bar = MagicMock(spec=QProgressBar)

        with patch('builtins.open', mock_open()), \
             patch('os.path.exists', return_value=False), \
             patch('os.makedirs'):

            result = export_manager.download_archive(
                ["id1", "id2"], "test_archive", 2048, mock_progress_bar
            )

            assert result == "paused"


class TestExportComponentResume:
    """Test export component resume functionality."""

    def test_save_export_state(self, export_component):
        """Test saving export state for resume."""
        selected_buckets = ["2023-01", "2023-02"]
        inputs = {"is_archived": False, "with_partners": True}
        archive_size_bytes = 1000000
        download_option = "Per Bucket"
        current_bucket_index = 1

        export_component.save_export_state(
            selected_buckets, inputs, archive_size_bytes,
            download_option, current_bucket_index
        )

        state = export_component.paused_export_state
        assert state is not None
        assert state['selected_buckets'] == selected_buckets
        assert state['inputs'] == inputs
        assert state['archive_size_bytes'] == archive_size_bytes
        assert state['download_option'] == download_option
        assert state['current_bucket_index'] == current_bucket_index

    def test_resume_export_no_state(self, export_component):
        """Test resume export when no paused state exists."""
        mock_logger = MagicMock()
        export_component.logger = mock_logger

        export_component.resume_export()

        mock_logger.append.assert_called_with("No paused export to resume.")

    def test_show_resume_button(self, export_component):
        """Test showing resume button - current implementation shows export button."""
        mock_logger = MagicMock()
        export_component.logger = mock_logger

        # Mock buttons
        export_component.stop_button = MagicMock()
        export_component.resume_button = MagicMock()
        export_component.export_button = MagicMock()

        # Test: Current implementation always shows export button
        mock_export_manager = MagicMock()
        export_component.export_manager = mock_export_manager

        export_component.show_resume_button()

        export_component.stop_button.hide.assert_called()
        export_component.export_button.show.assert_called()
        # Check that log messages were called (there are two messages)
        assert mock_logger.append.call_count == 2

    def test_check_for_resumable_downloads_exists(self, export_component, temp_output_dir):
        """Test checking for resumable downloads when they exist."""
        export_component.output_dir = temp_output_dir
        export_component.export_manager = MagicMock()

        # Create resume directory and metadata file
        resume_dir = os.path.join(temp_output_dir, ".archimmich_resume")
        os.makedirs(resume_dir)

        metadata_file = os.path.join(resume_dir, "test.resume.json")
        with open(metadata_file, 'w') as f:
            json.dump({"test": "data"}, f)

        result = export_component.check_for_resumable_downloads()
        assert result is True

    def test_check_for_resumable_downloads_none(self, export_component, temp_output_dir):
        """Test checking for resumable downloads when none exist."""
        export_component.output_dir = temp_output_dir
        export_component.export_manager = MagicMock()

        result = export_component.check_for_resumable_downloads()
        assert result is False


class TestIntegration:
    """Integration tests for resume functionality."""

    def test_full_resume_workflow(self, export_component, temp_output_dir):
        """Test complete pause and resume workflow."""
        export_component.output_dir = temp_output_dir
        export_component.logger = MagicMock()
        export_component.stop_button = MagicMock()
        export_component.resume_button = MagicMock()
        export_component.export_button = MagicMock()

        # Mock export manager
        mock_export_manager = MagicMock()
        mock_export_manager.api_manager.server_url = "http://test-server.com"
        mock_export_manager.check_range_header_support.return_value = True  # Mock Range header support
        export_component.export_manager = mock_export_manager

        # Test data
        selected_buckets = ["2023-01", "2023-02"]
        inputs = {"is_archived": False, "with_partners": True}
        archive_size_bytes = 1000000

        # Step 1: Save export state (simulating pause)
        export_component.save_export_state(
            selected_buckets, inputs, archive_size_bytes, "Per Bucket", 1
        )

        # Verify state is saved
        assert export_component.paused_export_state is not None
        assert export_component.paused_export_state['current_bucket_index'] == 1

        # Step 2: Show resume button
        export_component.show_resume_button()
        export_component.stop_button.hide.assert_called()
        export_component.export_button.show.assert_called()

        # Step 3: Test resume (mock the methods it calls)
        with patch.object(export_component, 'process_buckets_individually_resume') as mock_process, \
             patch.object(export_component, 'finalize_export') as mock_finalize:

            # Mock login manager
            export_component.login_manager = MagicMock()
            export_component.login_manager.api_manager = MagicMock()

            # Clear paused state to simulate successful completion
            def mock_process_side_effect(*args, **kwargs):
                export_component.paused_export_state = None
            mock_process.side_effect = mock_process_side_effect

            export_component.resume_export()

            # Verify resume process called with correct parameters
            mock_process.assert_called_once_with(selected_buckets, inputs, archive_size_bytes, 1)
            mock_finalize.assert_called_once()

            # Verify UI state changes
            export_component.resume_button.hide.assert_called()
            export_component.stop_button.show.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])