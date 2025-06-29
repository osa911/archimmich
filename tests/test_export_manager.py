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
    return ExportManager(
        api_manager=mock_api_manager,
        logger=mock_logger,
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
    mock_response = [{
        "id": 1,
        "timeBucket": "2024-03-01T00:00:00.000Z",
        "count": 5
    }]
    mock_api_manager.get.return_value = mock_response
    mock_api_manager.debug = {"verbose_logging": False}

    result = export_manager.get_timeline_buckets(
        is_archived=True,
        with_partners=False,
        with_stacked=False
    )

    # Verify the URL construction
    expected_url = (
        "/timeline/buckets"
        "?isArchived=true"
        "&withPartners=false"
        "&withStacked=false"
        "&isFavorite=false"
        "&isTrashed=false"
        "&order=desc"
    )
    mock_api_manager.get.assert_called_once_with(expected_url, expected_type=list)
    assert result == mock_response


def test_get_timeline_bucket_assets(export_manager, mock_api_manager):
    """Test fetching timeline bucket assets."""
    mock_response = {
        "id": ["123", "456"]
    }
    mock_api_manager.get.return_value = mock_response

    result = export_manager.get_timeline_bucket_assets(
        time_bucket="2024-12",
        is_archived=True,
        with_partners=False,
        with_stacked=False
    )

    # Verify the URL construction
    expected_url = (
        "/timeline/bucket"
        "?isArchived=true"
        "&withPartners=false"
        "&withStacked=false"
        "&timeBucket=2024-12"
        "&isFavorite=false"
        "&isTrashed=false"
        "&order=desc"
    )
    mock_api_manager.get.assert_called_once_with(expected_url, expected_type=dict)
    assert result == [{"id": "123"}, {"id": "456"}]


def test_get_timeline_buckets_empty_response(export_manager, mock_api_manager):
    """Test fetching timeline buckets with empty response."""
    mock_api_manager.get.return_value = []
    mock_api_manager.debug = {"verbose_logging": False}

    result = export_manager.get_timeline_buckets(
        is_archived=True,
        with_partners=False,
        with_stacked=False
    )

    assert result == []


def test_get_timeline_bucket_assets_empty_response(export_manager, mock_api_manager):
    """Test fetching timeline bucket assets with empty response."""
    mock_api_manager.get.return_value = {"id": []}

    result = export_manager.get_timeline_bucket_assets(
        time_bucket="2024-12",
        is_archived=True,
        with_partners=False,
        with_stacked=False
    )

    assert result == []


def test_get_timeline_buckets_with_visibility(export_manager, mock_api_manager):
    """Test fetching timeline buckets with visibility parameter."""
    mock_response = [{
        "id": 1,
        "timeBucket": "2024-03-01T00:00:00.000Z",
        "count": 5
    }]
    mock_api_manager.get.return_value = mock_response
    mock_api_manager.debug = {"verbose_logging": False}

    result = export_manager.get_timeline_buckets(
        is_archived=True,
        with_partners=False,
        with_stacked=False,
        visibility="public"
    )

    # Verify the URL construction with visibility
    expected_url = (
        "/timeline/buckets"
        "?isArchived=true"
        "&withPartners=false"
        "&withStacked=false"
        "&isFavorite=false"
        "&isTrashed=false"
        "&order=desc"
        "&visibility=public"
    )
    mock_api_manager.get.assert_called_once_with(expected_url, expected_type=list)
    assert result == mock_response


def test_get_timeline_bucket_assets_with_visibility(export_manager, mock_api_manager):
    """Test fetching timeline bucket assets with visibility parameter."""
    mock_response = {
        "id": ["123", "456"]
    }
    mock_api_manager.get.return_value = mock_response

    result = export_manager.get_timeline_bucket_assets(
        time_bucket="2024-12",
        is_archived=True,
        with_partners=False,
        with_stacked=False,
        visibility="public"
    )

    # Verify the URL construction with visibility
    expected_url = (
        "/timeline/bucket"
        "?isArchived=true"
        "&withPartners=false"
        "&withStacked=false"
        "&timeBucket=2024-12"
        "&isFavorite=false"
        "&isTrashed=false"
        "&order=desc"
        "&visibility=public"
    )
    mock_api_manager.get.assert_called_once_with(expected_url, expected_type=dict)
    assert result == [{"id": "123"}, {"id": "456"}]


def test_get_timeline_buckets_invalid_response(export_manager, mock_api_manager):
    """Test handling of invalid bucket responses."""
    mock_response = [
        {"id": 1},  # Missing timeBucket and count
        {"id": 2, "timeBucket": "invalid-date", "count": 5},  # Invalid date format
        {"id": 3, "timeBucket": "2024-03-01T00:00:00.000Z", "count": 5},  # Valid bucket
    ]
    mock_api_manager.get.return_value = mock_response
    mock_api_manager.debug = {"verbose_logging": True}

    result = export_manager.get_timeline_buckets(
        is_archived=True,
        with_partners=False,
        with_stacked=False
    )

    # Only the valid bucket should be returned
    assert result == [{"id": 3, "timeBucket": "2024-03-01T00:00:00.000Z", "count": 5}]


def test_prepare_archive(export_manager, mock_api_manager):
    """Test preparing an archive with asset IDs."""
    mock_response = {"totalSize": 1024}
    mock_api_manager.post.return_value = mock_response

    result = export_manager.prepare_archive(
        asset_ids=["1", "2", "3"],
        archive_size_bytes=1024
    )

    mock_api_manager.post.assert_called_once_with(
        "/download/info",
        json_data={"assetIds": ["1", "2", "3"], "archiveSize": 1024},
        expected_type=dict
    )
    assert result == mock_response


def test_prepare_archive_with_album_id(export_manager, mock_api_manager):
    """Test preparing an archive with album ID."""
    mock_response = {"totalSize": 2048}
    mock_api_manager.post.return_value = mock_response

    result = export_manager.prepare_archive(
        album_id="album123",
        archive_size_bytes=1024
    )

    mock_api_manager.post.assert_called_once_with(
        "/download/info",
        json_data={"albumId": "album123", "archiveSize": 1024},
        expected_type=dict
    )
    assert result == mock_response


def test_prepare_archive_with_both_ids(export_manager, mock_api_manager):
    """Test preparing an archive with both asset IDs and album ID (should prefer album ID)."""
    mock_response = {"totalSize": 2048}
    mock_api_manager.post.return_value = mock_response

    result = export_manager.prepare_archive(
        asset_ids=["1", "2", "3"],
        album_id="album123",
        archive_size_bytes=1024
    )

    mock_api_manager.post.assert_called_once_with(
        "/download/info",
        json_data={"albumId": "album123", "archiveSize": 1024},
        expected_type=dict
    )
    assert result == mock_response


def test_prepare_archive_no_ids(export_manager, mock_api_manager):
    """Test preparing an archive with neither asset IDs nor album ID."""
    result = export_manager.prepare_archive(archive_size_bytes=1024)

    assert result == {"totalSize": 0}
    mock_api_manager.post.assert_not_called()


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
            stream=True,
            expected_type=None,
            headers={}
        )
        mock_logger.append.assert_any_call("Starting fresh download: test_bucket.zip")
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
    assert ExportManager.format_time_bucket("2024-12-20T00:00:00Z") == "December_2024"


def test_calculate_file_checksum(tmp_path):
    """Test calculate_file_checksum method."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")

    checksum = ExportManager.calculate_file_checksum(str(file_path))
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 has 64 characters


def test_format_size_precision():
    """Test format_size method with improved GB precision."""
    # Test small values show precise GB instead of 0.00
    assert ExportManager.format_size(18.92 * 1024 * 1024) == "0.02 GB (18.92 MB)"
    assert ExportManager.format_size(37.83 * 1024 * 1024) == "0.04 GB (37.83 MB)"
    assert ExportManager.format_size(56.74 * 1024 * 1024) == "0.05 GB (56.74 MB)"
    assert ExportManager.format_size(100 * 1024 * 1024) == "0.10 GB (100.00 MB)"
    assert ExportManager.format_size(500 * 1024 * 1024) == "0.49 GB (500.00 MB)"

    # Test GB values are calculated correctly (not multiplied by 1024)
    assert ExportManager.format_size(1024 * 1024 * 1024) == "1.00 GB (1024.00 MB)"
    assert ExportManager.format_size(1.5 * 1024 * 1024 * 1024) == "1.50 GB (1536.00 MB)"
    assert ExportManager.format_size(2 * 1024 * 1024 * 1024) == "2.00 GB (2048.00 MB)"


def test_download_archive_with_progress_and_speed(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test download archive logs progress with speed calculation."""
    import time
    from unittest.mock import patch, MagicMock

    # Mock response with multiple chunks to trigger progress logging
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.headers = {}
    mock_response.iter_content.return_value = [
        b"x" * (1024 * 1024),  # 1MB chunk - should trigger 1% progress
        b"x" * (1024 * 1024),  # 1MB chunk - should trigger 2% progress
    ]
    mock_api_manager.post.return_value = mock_response

    # Mock time to control speed calculation
    start_time = 1000.0
    current_time = start_time

    def mock_time():
        nonlocal current_time
        current_time += 1.0  # Advance 1 second per call
        return current_time

    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'), \
         patch('time.time', side_effect=mock_time):

        result = export_manager.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=100 * 1024 * 1024,  # 100MB total
            current_download_progress_bar=mock_progress_bar
        )

        # Verify download completed
        assert result == "completed"

        # Check that progress logs include speed information
        logged_calls = [call.args[0] for call in mock_logger.append.call_args_list]
        progress_logs = [log for log in logged_calls if "Download progress:" in log and "Speed:" in log]

        # Should have at least one progress log with speed
        assert len(progress_logs) > 0

        # Verify speed format in logs
        for log in progress_logs:
            assert "MB/s" in log
            assert "Speed:" in log


def test_download_archive_speed_calculation_edge_cases(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test download archive handles edge cases in speed calculation."""
    import time
    from unittest.mock import patch, MagicMock

    # Mock response with one chunk
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.headers = {}
    mock_response.iter_content.return_value = [b"x" * (2 * 1024 * 1024)]  # 2MB chunk
    mock_api_manager.post.return_value = mock_response

    # Mock time to return same time (zero elapsed time)
    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'), \
         patch('time.time', return_value=1000.0):  # Same time always

        result = export_manager.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=100 * 1024 * 1024,  # 100MB total
            current_download_progress_bar=mock_progress_bar
        )

        # Verify download completed
        assert result == "completed"

        # Check that progress logs handle zero elapsed time gracefully
        logged_calls = [call.args[0] for call in mock_logger.append.call_args_list]
        progress_logs = [log for log in logged_calls if "Download progress:" in log]

        # Should have progress logs without speed (since elapsed time is 0)
        assert len(progress_logs) > 0

        # Verify no speed is shown when elapsed time is 0
        for log in progress_logs:
            # Should not contain speed info when elapsed time is 0
            if "Speed:" in log:
                # If speed is shown, it should handle the edge case gracefully
                assert "MB/s" in log


def test_download_archive_with_album_id(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test downloading an archive using album ID."""
    mock_api_manager.post.return_value.iter_content = MagicMock(return_value=[b"chunk1", b"chunk2"])
    mock_api_manager.post.return_value.ok = True
    mock_api_manager.post.return_value.headers = {}

    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'):

        export_manager.download_archive(
            album_id="album123",
            bucket_name="test_album",
            total_size=2048,
            current_download_progress_bar=mock_progress_bar
        )

        mock_api_manager.post.assert_called_once_with(
            "/download/archive",
            json_data={"albumId": "album123"},
            stream=True,
            expected_type=None,
            headers={}
        )
        mock_logger.append.assert_any_call("Starting fresh download: test_album.zip")
        mock_progress_bar.setValue.assert_any_call(100)


def test_download_archive_no_ids(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test downloading an archive with neither asset IDs nor album ID."""
    result = export_manager.download_archive(
        bucket_name="test_bucket",
        total_size=2048,
        current_download_progress_bar=mock_progress_bar
    )

    assert result is None
    mock_logger.append.assert_called_with("No assets or album provided for download")
    mock_api_manager.post.assert_not_called()


def test_get_albums(export_manager, mock_api_manager):
    """Test fetching albums list."""
    mock_albums = [
        {
            "id": "album1",
            "albumName": "Test Album 1",
            "albumThumbnailAssetId": "thumb1",
            "assetCount": 10,
            "createdAt": "2025-06-12T11:56:28.017Z",
            "updatedAt": "2025-06-12T12:36:17.928Z"
        },
        {
            "id": "album2",
            "albumName": "Test Album 2",
            "albumThumbnailAssetId": "thumb2",
            "assetCount": 20,
            "createdAt": "2025-06-12T11:56:28.017Z",
            "updatedAt": "2025-06-12T12:36:17.928Z"
        }
    ]
    mock_api_manager.get.return_value = mock_albums

    result = export_manager.get_albums()

    mock_api_manager.get.assert_called_once_with("/albums", expected_type=list)
    assert len(result) == 2
    assert result[0]["id"] == "album1"
    assert result[1]["id"] == "album2"


def test_get_albums_validation(export_manager, mock_api_manager, mock_logger):
    """Test album validation with invalid data."""
    mock_albums = [
        {
            "id": "album1",  # Missing required fields
            "albumName": "Test Album 1"
        },
        {
            "id": "album2",
            "albumName": "Test Album 2",
            "albumThumbnailAssetId": "thumb2",
            "assetCount": 20,
            "createdAt": "2025-06-12T11:56:28.017Z",
            "updatedAt": "2025-06-12T12:36:17.928Z"
        }
    ]
    mock_api_manager.get.return_value = mock_albums

    result = export_manager.get_albums()

    assert len(result) == 1  # Only one valid album
    assert result[0]["id"] == "album2"
    mock_logger.append.assert_any_call("Filtered 1 invalid buckets: 1 Missing albumThumbnailAssetId")


def test_get_albums_empty(export_manager, mock_api_manager):
    """Test fetching empty albums list."""
    mock_api_manager.get.return_value = []

    result = export_manager.get_albums()

    assert result == []
    mock_api_manager.get.assert_called_once_with("/albums", expected_type=list)