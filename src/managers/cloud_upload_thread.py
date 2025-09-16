from PyQt5.QtCore import QThread, pyqtSignal


class CloudUploadThread(QThread):
    """
    Thread for handling cloud uploads in the background to keep UI responsive.
    """
    progress_updated = pyqtSignal(int, str)  # progress, message
    upload_completed = pyqtSignal(bool, str)  # success, message

    def __init__(self, export_manager, asset_ids, album_id, bucket_name, total_size, cloud_config, logger):
        super().__init__()
        self.export_manager = export_manager
        self.asset_ids = asset_ids
        self.album_id = album_id
        self.bucket_name = bucket_name
        self.total_size = total_size
        self.cloud_config = cloud_config
        self.logger = logger
        self.should_stop = False

    def log(self, message):
        """Log a message using thread-safe signal."""
        self.logger.append(message)

    def run(self):
        try:
            # Check for stop signal before starting
            if self.should_stop:
                self.upload_completed.emit(False, "Upload cancelled by user")
                return

            # Prepare payload
            payload = {}
            if self.album_id:
                # For albums, we need to fetch the asset IDs first
                album_asset_ids = self.export_manager.get_album_assets(self.album_id)
                if not album_asset_ids:
                    self.upload_completed.emit(False, f"No assets found for album {self.album_id}")
                    return
                payload["assetIds"] = album_asset_ids
            else:
                payload["assetIds"] = self.asset_ids

            # Check for stop signal after fetching assets
            if self.should_stop:
                self.upload_completed.emit(False, "Upload cancelled by user")
                return

            # Log the start of the process
            self.log(f"Starting cloud upload for {self.bucket_name}.zip")
            self.log(f"Connecting to Immich server to get download stream...")

            # Get download stream from Immich
            response = self.export_manager.api_manager.post(
                "/download/archive",
                json_data=payload,
                stream=True,
                expected_type=None,
                headers={}
            )

            if not response or not response.ok:
                error_msg = f"Failed to start download: {response.status_code if response else 'No response'}"
                self.log(error_msg)
                self.upload_completed.emit(False, error_msg)
                return

            # Check for stop signal after getting response
            if self.should_stop:
                self.upload_completed.emit(False, "Upload cancelled by user")
                return

            self.log(f"Successfully connected to Immich server, starting upload...")

            # Create progress callback wrapper that checks for stop signal
            def progress_wrapper(progress, uploaded_bytes, total_bytes, speed):
                if self.should_stop:
                    return False  # Signal to stop the upload

                # Format speed like local downloads
                speed_mb = speed / (1024 ** 2)  # Convert from bytes/s to MB/s
                speed_text = f", Speed: {speed_mb:.2f} MB/s" if speed > 0 else ""

                self.progress_updated.emit(int(progress), f"Uploading: {self.bucket_name} - {progress:.1f}% ({self.export_manager.format_size(uploaded_bytes)}/{self.export_manager.format_size(total_bytes)}){speed_text}")
                return True  # Continue upload

            # Upload stream directly to cloud
            cloud_type = self.cloud_config.get('type')
            self.log(f"Starting {cloud_type.upper()} upload to {self.cloud_config.get('url', 'cloud storage')}")

            if cloud_type == 'webdav':
                # Create remote directory if specified
                remote_dir = self.cloud_config.get('remote_directory', '')
                if remote_dir:
                    self.log(f"Creating remote directory: {remote_dir}")
                    self.export_manager.cloud_storage_manager.create_webdav_directory(
                        self.cloud_config['url'],
                        self.cloud_config['username'],
                        self.cloud_config['password'],
                        remote_dir,
                        self.cloud_config.get('auth_type', 'basic')
                    )
                    self.log(f"Remote directory created successfully")

                # Construct remote path
                if remote_dir:
                    remote_path = f"{remote_dir}/{self.bucket_name}.zip"
                else:
                    remote_path = f"{self.bucket_name}.zip"

                self.log(f"Uploading to remote path: {remote_path}")
                self.log(f"Starting stream upload with total size: {self.export_manager.format_size(self.total_size)}")

                # Upload stream directly
                upload_success, upload_message = self.export_manager.cloud_storage_manager.upload_stream_to_webdav(
                    response,
                    self.cloud_config['url'],
                    self.cloud_config['username'],
                    self.cloud_config['password'],
                    remote_path,
                    self.cloud_config.get('auth_type', 'basic'),
                    progress_wrapper,
                    self.total_size
                )

            elif cloud_type == 's3':
                # S3 streaming upload
                remote_prefix = self.cloud_config.get('remote_prefix', '')
                if remote_prefix:
                    remote_path = f"{remote_prefix}/{self.bucket_name}.zip"
                else:
                    remote_path = f"{self.bucket_name}.zip"

                self.log(f"Uploading to S3 path: {remote_path}")
                self.log(f"Starting S3 stream upload with total size: {self.export_manager.format_size(self.total_size)}")

                # Upload stream directly to S3
                upload_success, upload_message = self.export_manager.cloud_storage_manager.upload_stream_to_s3(
                    response,
                    self.cloud_config['endpoint_url'],
                    self.cloud_config['access_key'],
                    self.cloud_config['secret_key'],
                    self.cloud_config['bucket_name'],
                    remote_path,
                    self.cloud_config.get('region', 'us-east-1'),
                    progress_wrapper,
                    self.total_size
                )
            else:
                upload_success, upload_message = False, f"Unsupported cloud storage type: {cloud_type}"

            self.log(f"{cloud_type.upper()} upload completed. Success: {upload_success}, Message: {upload_message}")

            # Check if upload was cancelled
            if self.should_stop:
                self.upload_completed.emit(False, "Upload cancelled by user")
                return

            if upload_success:
                self.log(f"Successfully uploaded {self.bucket_name}.zip to cloud storage")
                self.upload_completed.emit(True, "Upload completed successfully")
            else:
                self.log(f"Failed to upload to cloud storage: {upload_message}")
                self.upload_completed.emit(False, upload_message)

        except Exception as e:
            if self.should_stop:
                self.upload_completed.emit(False, "Upload cancelled by user")
            else:
                error_msg = f"Cloud streaming error: {str(e)}"
                self.log(error_msg)
                self.upload_completed.emit(False, error_msg)

    def stop(self):
        """Stop the upload thread."""
        self.should_stop = True
