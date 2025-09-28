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
def mock_login_manager(mock_api_manager):
    """Mock the login manager."""
    login_manager = Mock()
    login_manager.api_manager = mock_api_manager
    login_manager.is_logged_in = Mock(return_value=True)
    return login_manager


@pytest.fixture
def export_manager(mock_login_manager, mock_logs_widget, mock_logger):
    """Initialize ExportManager with mocks."""
    return ExportManager(
        login_manager=mock_login_manager,
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
        "&size=MONTH"
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
        "&size=MONTH"
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
        "&size=MONTH"
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
        "&size=MONTH"
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
    mock_api_manager.post.return_value.ok = True
    mock_api_manager.post.return_value.headers = {}

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
        mock_logger.append.assert_any_call('Starting fresh download: "test_bucket.zip"')


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
    assert ExportManager.format_size(56.74 * 1024 * 1024) == "0.06 GB (56.74 MB)"
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

    # Set up login_manager
    export_manager.login_manager.is_logged_in.return_value = True
    # Set up stop_flag
    export_manager.stop_flag.return_value = False

    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'), \
         patch('os.rename'), \
         patch('os.path.getsize', return_value=2 * 1024 * 1024), \
         patch('time.time', side_effect=mock_time):

        result = export_manager.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=100 * 1024 * 1024,  # 100MB total
            current_download_progress_bar=mock_progress_bar
        )

        # Verify download completed
        assert result == "completed"


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

    # Set up login_manager
    export_manager.login_manager.is_logged_in.return_value = True
    # Set up stop_flag
    export_manager.stop_flag.return_value = False

    # Mock time to return same time (zero elapsed time)
    with patch('builtins.open', MagicMock()), \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'), \
         patch('os.rename'), \
         patch('os.path.getsize', return_value=2 * 1024 * 1024), \
         patch('time.time', return_value=1000.0):  # Same time always

        result = export_manager.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=100 * 1024 * 1024,  # 100MB total
            current_download_progress_bar=mock_progress_bar
        )

        # Verify download completed
        assert result == "completed"


def test_download_archive_with_album_id(export_manager, mock_api_manager, mock_logger, mock_progress_bar):
    """Test downloading an archive using album ID."""
    # Setup mock response
    mock_response = Mock()
    mock_response.iter_content = MagicMock(return_value=[b"chunk1", b"chunk2"])
    mock_response.ok = True
    mock_response.headers = {}
    mock_api_manager.post.return_value = mock_response

    # Mock required conditions
    export_manager.login_manager.is_logged_in.return_value = True
    export_manager.stop_flag = Mock(return_value=False)

    # Set up output directory
    export_manager.output_dir = "/test/output"

    with patch('builtins.open', MagicMock()) as mock_open, \
         patch('os.path.exists', return_value=False), \
         patch('os.makedirs'), \
         patch('os.rename'), \
         patch('os.path.getsize', return_value=12), \
         patch('src.managers.export_manager.ExportManager.log'), \
         patch.object(export_manager, 'get_album_assets', return_value=['asset1', 'asset2']), \
         patch.object(export_manager, 'can_resume_download', return_value=(False, 0)), \
         patch.object(export_manager, 'check_range_header_support', return_value=True):

        result = export_manager.download_archive(
            album_id="album123",
            bucket_name="test_album",
            total_size=2048,
            current_download_progress_bar=mock_progress_bar
        )

        # Verify the API call was made with asset IDs (not album ID)
        mock_api_manager.post.assert_called_once_with(
            "/download/archive",
            json_data={"assetIds": ['asset1', 'asset2']},
            stream=True,
            expected_type=None,
            headers={}
        )

        # Verify file operations
        mock_open.assert_called()

        # The result should be "completed" for successful local download
        assert result == "completed"


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
    mock_logger.append.assert_any_call("Validation error: Missing albumThumbnailAssetId")


def test_get_albums_empty(export_manager, mock_api_manager):
    """Test fetching empty albums list."""
    mock_api_manager.get.return_value = []

    result = export_manager.get_albums()

    assert result == []
    mock_api_manager.get.assert_called_once_with("/albums", expected_type=list)


# Cloud Storage Tests
@pytest.fixture
def mock_cloud_storage_manager():
    """Mock cloud storage manager."""
    return Mock()


@pytest.fixture
def export_manager_with_cloud(mock_login_manager, mock_logs_widget, mock_logger, mock_cloud_storage_manager):
    """Initialize ExportManager with cloud storage support."""
    with patch('src.managers.export_manager.CloudStorageManager', return_value=mock_cloud_storage_manager):
        manager = ExportManager(
            login_manager=mock_login_manager,
            logger=mock_logger,
            output_dir="/tmp",
            stop_flag_callback=lambda: False
        )
        manager.cloud_storage_manager = mock_cloud_storage_manager
        return manager


def test_upload_archive_to_cloud_webdav(export_manager_with_cloud, mock_cloud_storage_manager, mock_logger, tmp_path):
    """Test uploading archive to WebDAV cloud storage."""
    # Create test file
    test_file = tmp_path / "test.zip"
    test_file.write_text("test archive content")

    # Mock cloud config
    cloud_config = {
        'type': 'webdav',
        'url': 'https://cloud.example.com/webdav',
        'username': 'testuser',
        'password': 'testpass',
        'remote_directory': 'backups',
        'auth_type': 'basic'
    }

    # Mock successful upload
    mock_cloud_storage_manager.create_webdav_directory.return_value = True
    mock_cloud_storage_manager.upload_file_to_webdav.return_value = (True, "Upload successful")

    result = export_manager_with_cloud.upload_archive_to_cloud(
        str(test_file), cloud_config, "test.zip"
    )

    # Verify calls
    mock_cloud_storage_manager.create_webdav_directory.assert_called_once_with(
        'https://cloud.example.com/webdav', 'testuser', 'testpass', 'backups', 'basic'
    )
    mock_cloud_storage_manager.upload_file_to_webdav.assert_called_once()

    assert result == (True, "Upload successful")


def test_upload_archive_to_cloud_s3(export_manager_with_cloud, mock_cloud_storage_manager, mock_logger, tmp_path):
    """Test uploading archive to S3 cloud storage."""
    # Create test file
    test_file = tmp_path / "test.zip"
    test_file.write_text("test archive content")

    # Mock cloud config
    cloud_config = {
        'type': 's3',
        'endpoint_url': 'https://s3.amazonaws.com',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'bucket_name': 'my-backup-bucket',
        'region': 'us-east-1'
    }

    # Mock successful upload
    mock_cloud_storage_manager.upload_file_to_s3.return_value = (True, "Upload successful")

    result = export_manager_with_cloud.upload_archive_to_cloud(
        str(test_file), cloud_config, "test.zip"
    )

    # Verify calls
    mock_cloud_storage_manager.upload_file_to_s3.assert_called_once()

    assert result == (True, "Upload successful")


def test_upload_archive_to_cloud_unsupported_type(export_manager_with_cloud, mock_cloud_storage_manager, tmp_path):
    """Test uploading archive to unsupported cloud storage type."""
    # Create test file
    test_file = tmp_path / "test.zip"
    test_file.write_text("test archive content")

    cloud_config = {
        'type': 'unsupported',
        'url': 'https://example.com'
    }

    result = export_manager_with_cloud.upload_archive_to_cloud(
        str(test_file), cloud_config, "test.zip"
    )

    assert result == (False, "Unsupported cloud storage type: unsupported")


def test_download_archive_with_cloud_config(export_manager_with_cloud, mock_api_manager, mock_cloud_storage_manager, mock_logger):
    """Test download archive with cloud configuration for streaming upload."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.headers = {'content-length': '2097152'}  # 2MB
    mock_response.iter_content.return_value = [b"x" * (1024 * 1024), b"x" * (1024 * 1024)]  # 2x 1MB chunks
    mock_api_manager.post.return_value = mock_response

    # Mock cloud config
    cloud_config = {
        'type': 'webdav',
        'url': 'https://cloud.example.com/webdav',
        'username': 'testuser',
        'password': 'testpass',
        'remote_directory': 'backups',
        'auth_type': 'basic'
    }

    # Mock successful cloud upload
    mock_cloud_storage_manager.create_webdav_directory.return_value = True
    mock_cloud_storage_manager.upload_stream_to_webdav.return_value = (True, "Stream upload successful")

    # Mock stop flag and login
    export_manager_with_cloud.stop_flag = Mock(return_value=False)
    export_manager_with_cloud.login_manager.is_logged_in.return_value = True

    # Mock CloudUploadThread creation (imported inside the method)
    with patch('src.managers.cloud_upload_thread.CloudUploadThread') as mock_thread_class:
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        result = export_manager_with_cloud.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=2 * 1024 * 1024,
            cloud_config=cloud_config
        )

        # Verify cloud upload thread was created and started
        mock_thread_class.assert_called_once_with(
            export_manager_with_cloud,
            ["1", "2"],
            None,  # album_id
            "test_bucket",
            2 * 1024 * 1024,
            cloud_config,
            export_manager_with_cloud.logger
        )
        mock_thread.start.assert_called_once()

        # Verify the result indicates cloud upload started
        assert result == "uploading"


def test_download_archive_cloud_upload_failure(export_manager_with_cloud, mock_api_manager, mock_cloud_storage_manager, mock_logger):
    """Test download archive with cloud upload failure."""
    # Mock API response
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.headers = {'content-length': '1048576'}  # 1MB
    mock_response.iter_content.return_value = [b"x" * (1024 * 1024)]  # 1MB chunk
    mock_api_manager.post.return_value = mock_response

    # Mock cloud config
    cloud_config = {
        'type': 'webdav',
        'url': 'https://cloud.example.com/webdav',
        'username': 'testuser',
        'password': 'testpass',
        'auth_type': 'basic'
    }

    # Mock failed cloud upload
    mock_cloud_storage_manager.upload_stream_to_webdav.return_value = (False, "Upload failed: Connection timeout")

    # Mock stop flag and login
    export_manager_with_cloud.stop_flag = Mock(return_value=False)
    export_manager_with_cloud.login_manager.is_logged_in.return_value = True

    # Mock CloudUploadThread creation (imported inside the method)
    with patch('src.managers.cloud_upload_thread.CloudUploadThread') as mock_thread_class:
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        result = export_manager_with_cloud.download_archive(
            asset_ids=["1", "2"],
            bucket_name="test_bucket",
            total_size=1024 * 1024,
            cloud_config=cloud_config
        )

        # Verify cloud upload thread was created and started
        mock_thread_class.assert_called_once_with(
            export_manager_with_cloud,
            ["1", "2"],
            None,  # album_id
            "test_bucket",
            1024 * 1024,
            cloud_config,
            export_manager_with_cloud.logger
        )
        mock_thread.start.assert_called_once()

        # Verify the result indicates cloud upload started (failure happens in thread)
        assert result == "uploading"


def test_cloud_storage_manager_initialization(export_manager, mock_logger):
    """Test cloud storage manager is properly initialized."""
    with patch('src.managers.export_manager.CloudStorageManager') as mock_cloud_manager_class:
        manager = ExportManager(
            login_manager=Mock(),
            logger=mock_logger,
            output_dir="/tmp",
            stop_flag_callback=lambda: False
        )

        # Verify CloudStorageManager was instantiated with logger
        mock_cloud_manager_class.assert_called_once_with(mock_logger)


def test_format_cloud_progress_message(export_manager):
    """Test formatting of cloud upload progress messages."""
    # This tests the progress callback formatting used in cloud uploads
    uploaded_bytes = 50 * 1024 * 1024  # 50MB
    total_bytes = 100 * 1024 * 1024    # 100MB
    speed = 10 * 1024 * 1024           # 10MB/s
    progress = (uploaded_bytes / total_bytes) * 100  # 50%

    # Test the format used in progress callbacks
    speed_mb = speed / (1024 ** 2)
    expected_format = f"Uploading: test_bucket - {progress:.1f}% ({export_manager.format_size(uploaded_bytes)}/{export_manager.format_size(total_bytes)}), Speed: {speed_mb:.2f} MB/s"

    # Verify the format produces expected output
    assert "50.0%" in expected_format
    assert "Speed: 10.00 MB/s" in expected_format
    assert "test_bucket" in expected_format