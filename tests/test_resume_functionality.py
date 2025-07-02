"""
Tests for download resume functionality in ArchImmich.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, mock_open, call
from PyQt5.QtWidgets import QApplication, QProgressBar, QTabWidget, QWidget, QPushButton, QLabel

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
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QProgressBar, QVBoxLayout, QRadioButton, QButtonGroup, QLineEdit, QCheckBox, QTabWidget

    # Skip Qt-dependent tests in headless environment
    if 'pytest' in sys.modules and not QApplication.instance():
        try:
            app = QApplication([])
        except Exception:
            pytest.skip("Qt GUI not available")

    login_manager = MagicMock(spec=LoginManager)

    # Create the component
    component = ExportComponent(login_manager)
    component.output_dir = "/tmp/test"

    # Initialize timeline main area
    component.timeline_main_area = QWidget()
    component.timeline_main_area.output_dir = "/tmp/test"
    component.timeline_main_area.output_dir_label = QLabel()
    component.timeline_main_area.output_dir_button = QPushButton()
    component.timeline_main_area.export_button = QPushButton()
    component.timeline_main_area.stop_button = QPushButton()
    component.timeline_main_area.resume_button = QPushButton()
    component.timeline_main_area.progress_bar = MagicMock()
    component.timeline_main_area.current_download_progress_bar = MagicMock()
    component.timeline_main_area.archives_section = QWidget()
    component.timeline_main_area.archives_display = MagicMock()

    # Initialize albums main area
    component.albums_main_area = QWidget()
    component.albums_main_area.output_dir = "/tmp/test"
    component.albums_main_area.output_dir_label = QLabel()
    component.albums_main_area.output_dir_button = QPushButton()
    component.albums_main_area.export_button = QPushButton()
    component.albums_main_area.stop_button = QPushButton()
    component.albums_main_area.resume_button = QPushButton()
    component.albums_main_area.progress_bar = MagicMock()
    component.albums_main_area.current_download_progress_bar = MagicMock()
    component.albums_main_area.archives_section = QWidget()
    component.albums_main_area.archives_display = MagicMock()

    # Initialize filter controls
    component.is_archived_check = QCheckBox("Is Archived?")
    component.with_partners_check = QCheckBox("With Partners?")
    component.with_stacked_check = QCheckBox("With Stacked?")
    component.is_favorite_check = QCheckBox("Is Favorite?")
    component.is_trashed_check = QCheckBox("Is Trashed?")

    # Initialize visibility radio buttons
    component.visibility_none = QRadioButton("Not specified")
    component.visibility_archive = QRadioButton("Archive")
    component.visibility_timeline = QRadioButton("Timeline")
    component.visibility_hidden = QRadioButton("Hidden")
    component.visibility_locked = QRadioButton("Locked")
    component.visibility_group = QButtonGroup()
    component.visibility_group.addButton(component.visibility_none)
    component.visibility_group.addButton(component.visibility_archive)
    component.visibility_group.addButton(component.visibility_timeline)
    component.visibility_group.addButton(component.visibility_hidden)
    component.visibility_group.addButton(component.visibility_locked)
    component.visibility_none.setChecked(True)

    # Initialize download options
    component.download_group = QButtonGroup()
    component.download_per_bucket = QRadioButton("Per bucket")
    component.download_combined = QRadioButton("Combined")
    component.download_group.addButton(component.download_per_bucket)
    component.download_group.addButton(component.download_combined)
    component.download_per_bucket.setChecked(True)

    # Initialize archive size field
    component.archive_size_field = QLineEdit()
    component.archive_size_field.setText("4")

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
    """Test resume functionality in ExportComponent."""

    @pytest.fixture
    def export_component(self):
        """Create an ExportComponent for testing."""
        from src.ui.components.export_component import ExportComponent
        login_manager = MagicMock()
        logger = MagicMock()
        component = ExportComponent(login_manager, logger)

        # Initialize required attributes
        component.tab_widget = QTabWidget()

        # Timeline tab
        component.timeline_main_area = QWidget()
        component.timeline_main_area.order_button = QPushButton("↓")
        component.timeline_main_area.output_dir = ""
        component.timeline_main_area.output_dir_label = QLabel()
        component.timeline_main_area.output_dir_button = QPushButton()
        component.timeline_main_area.export_button = QPushButton()
        component.timeline_main_area.stop_button = QPushButton()
        component.timeline_main_area.resume_button = QPushButton()
        component.timeline_main_area.progress_bar = MagicMock()
        component.timeline_main_area.current_download_progress_bar = MagicMock()
        component.timeline_main_area.archives_section = QWidget()
        component.timeline_main_area.archives_display = MagicMock()

        return component

    def test_resume_export_no_state(self, export_component):
        """Test resume export when no state exists."""
        # Setup
        export_component.timeline_main_area.export_button = MagicMock()
        export_component.timeline_main_area.resume_button = MagicMock()
        export_component.timeline_main_area.stop_button = MagicMock()
        export_component.timeline_main_area.output_dir_button = MagicMock()
        export_component.albums_main_area.export_button = MagicMock()
        export_component.albums_main_area.resume_button = MagicMock()
        export_component.albums_main_area.stop_button = MagicMock()
        export_component.albums_main_area.output_dir_button = MagicMock()
        export_component.logger = MagicMock()

        # Test for timeline tab
        export_component.resume_export(export_component.timeline_main_area)
        export_component.logger.append.assert_called_with("No paused export to resume.")

        # Test for albums tab
        export_component.resume_export(export_component.albums_main_area)
        export_component.logger.append.assert_called_with("No paused export to resume.")

    def test_show_resume_button(self, export_component):
        """Test showing resume button."""
        # Setup export manager with mock server URL
        mock_export_manager = MagicMock()
        mock_export_manager.api_manager.server_url = "http://test-server.com"
        export_component.export_manager = mock_export_manager
        export_component.login_manager.is_logged_in.return_value = True
        export_component.logger = MagicMock()

        # Mock UI components
        export_component.timeline_main_area.stop_button = MagicMock()
        export_component.timeline_main_area.export_button = MagicMock()
        export_component.timeline_main_area.output_dir_button = MagicMock()

        # Test for timeline tab
        export_component.show_resume_button(export_component.timeline_main_area)
        export_component.timeline_main_area.stop_button.hide.assert_called_once()
        export_component.timeline_main_area.output_dir_button.show.assert_called_once()
        export_component.logger.append.assert_any_call("Export paused. Server doesn't support resume functionality.")
        export_component.logger.append.assert_any_call("Click 'Export' to restart. Already downloaded files will be skipped automatically.")

    def test_check_for_resumable_downloads_exists(self, export_component, temp_output_dir):
        """Test checking for resumable downloads when they exist."""
        # Setup
        export_component.timeline_main_area.output_dir = temp_output_dir
        export_component.export_manager = MagicMock()  # Add mock export manager

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
        export_component.timeline_main_area.output_dir = temp_output_dir
        result = export_component.check_for_resumable_downloads()
        assert result is False


class TestIntegration:
    """Integration tests for resume functionality."""

    def test_full_resume_workflow(self, export_component, temp_output_dir):
        """Test complete pause and resume workflow."""
        export_component.timeline_main_area.output_dir = temp_output_dir
        export_component.logger = MagicMock()

        # Mock export manager
        mock_export_manager = MagicMock()
        mock_export_manager.api_manager.server_url = "http://test-server.com"
        mock_export_manager.check_range_header_support.return_value = True  # Mock Range header support
        export_component.export_manager = mock_export_manager
        export_component.login_manager.is_logged_in.return_value = True

        # Mock UI components
        export_component.timeline_main_area.stop_button = MagicMock()
        export_component.timeline_main_area.resume_button = MagicMock()
        export_component.timeline_main_area.export_button = MagicMock()
        export_component.timeline_main_area.output_dir_button = MagicMock()

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
        export_component.show_resume_button(export_component.timeline_main_area)
        export_component.timeline_main_area.stop_button.hide.assert_called_once()
        export_component.timeline_main_area.output_dir_button.show.assert_called_once()
        export_component.logger.append.assert_any_call("Export paused. Server doesn't support resume functionality.")
        export_component.logger.append.assert_any_call("Click 'Export' to restart. Already downloaded files will be skipped automatically.")


if __name__ == "__main__":
    pytest.main([__file__])