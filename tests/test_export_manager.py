import pytest
import time
from unittest.mock import Mock, MagicMock, call, patch
from src.managers.export_manager import ExportManager


# Fixtures
@pytest.fixture
def mock_api_manager():
    """Mock the API manager."""
    return Mock()


@pytest.fixture
def mock_logs_widget():
    """Mock the logs widget (e.g., QTextEdit)."""
    return Mock()


@pytest.fixture
def mock_progress_bar():
    """Mock progress bar widget."""
    return Mock()


@pytest.fixture
def mock_logger():
    """Mock the Logger class."""
    with patch('src.utils.helpers.Logger') as mock:
        # Configure the mock to use test_mode=True
        instance = mock.return_value
        instance.test_mode = True
        yield instance


@pytest.fixture
def export_manager(mock_api_manager, mock_logs_widget, mock_logger):
    """Initialize ExportManager with mocks."""
    with patch('src.managers.export_manager.Logger', return_value=mock_logger):
        return ExportManager(
            api_manager=mock_api_manager,
            logs_widget=mock_logs_widget,
            output_dir="/tmp",
            stop_flag_callback=lambda: False
        )


# Test Cases
def test_log(export_manager, mock_logger):
    """Test the log method."""
    export_manager.log("Test message")
    mock_logger.append.assert_called_once_with("Test message")


def test_get_timeline_buckets(export_manager, mock_api_manager):
    """Test fetching timeline buckets."""
    mock_api_manager.get.return_value.json.return_value = [{"id": 1}]

    result = export_manager.get_timeline_buckets(
        is_archived=True,
        size="MONTH",
        with_partners=False,
        with_stacked=False
    )

    assert result == [{"id": 1}]
    mock_api_manager.get.assert_called_once_with(
        "/timeline/buckets?isArchived=true&size=MONTH&withPartners=false&withStacked=false"
    )


def test_get_timeline_bucket_assets(export_manager, mock_api_manager):
    """Test fetching timeline bucket assets."""
    mock_api_manager.get.return_value.json.return_value = [{"assetId": "123"}]

    result = export_manager.get_timeline_bucket_assets(
        time_bucket="2024-12",
        is_archived=True,
        size="MONTH",
        with_partners=False,
        with_stacked=False
    )

    assert result == [{"assetId": "123"}]
    mock_api_manager.get.assert_called_once_with(
        "/timeline/bucket?isArchived=true&size=MONTH&withPartners=false&withStacked=false&timeBucket=2024-12"
    )


def test_prepare_archive(export_manager, mock_api_manager):
    """Test preparing an archive."""
    mock_api_manager.post.return_value.json.return_value = {"totalSize": 1024}

    result = export_manager.prepare_archive(
        asset_ids=["1", "2", "3"],
        archive_size_bytes=1024
    )

    assert result == {"totalSize": 1024}
    mock_api_manager.post.assert_called_once_with(
        "/download/info",
        json_data={"assetIds": ["1", "2", "3"], "archiveSize": 1024}
    )


def test_download_archive(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test downloading an archive."""
    mock_api_manager.post.return_value.iter_content = MagicMock(return_value=[b"chunk1", b"chunk2"])

    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'):

        export_manager.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=2048,
            current_download_progress_bar=mock_progress_bar
        )

        mock_api_manager.post.assert_called_once_with(
            "/download/archive",
            json_data={"assetIds": ["1", "2"]},
            stream=True
        )
        mock_logger.append.assert_any_call("Downloading archive: test_bucket.zip")
        mock_progress_bar.setValue.assert_any_call(100)


def test_log_download_progress(export_manager, mock_logger):
    """Test log_download_progress method."""
    # Simulate a non-zero elapsed time
    start_time = time.time() - 1  # 1 second elapsed

    export_manager.log_download_progress(1024 * 1024, start_time)
    mock_logger.append.assert_called_once_with("Downloaded: 0.00 GB (1.00 MB), Speed: 1.00 MB/s")


def test_format_size():
    """Test format_size method."""
    assert ExportManager.format_size(1024) == "0.00 GB (0.00 MB) (1.00 KB)"
    assert ExportManager.format_size(1024 * 1024) == "0.00 GB (1.00 MB)"
    assert ExportManager.format_size(1024 * 1024 * 1024) == "1.00 GB (1024.00 MB)"
    assert ExportManager.format_size(512) == "0.00 GB (0.00 MB) (0.50 KB)"
    assert ExportManager.format_size(1) == "0.00 GB (0.00 MB) (0.00 KB)"


def test_format_time_bucket():
    """Test format_time_bucket method."""
    assert ExportManager.format_time_bucket("2024-12-20T00:00:00Z", format="MONTH") == "December_2024"
    assert ExportManager.format_time_bucket("2024-12-20T00:00:00Z", format="DAY") == "20.12.2024"


def test_calculate_file_checksum(tmp_path):
    """Test calculate_file_checksum method."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")

    checksum = ExportManager.calculate_file_checksum(str(file_path))
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 has 64 characters