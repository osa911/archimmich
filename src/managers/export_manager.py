import os
import time
import hashlib
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from src.utils.helpers import Logger

class ExportManager:
    def __init__(self, api_manager, logs_widget, output_dir, stop_flag_callback):
        """
        Args:
            api_manager (APIManager): Instance of APIManager for API calls.
            logs_widget (QTextEdit or similar): Widget for logging messages.
            output_dir (str): Directory where the archives will be saved.
            stop_flag_callback (callable): A function that returns True if stop is requested.
        """
        self.api_manager = api_manager
        self.logger = Logger(logs_widget)
        self.output_dir = output_dir
        self.stop_flag = stop_flag_callback
        self.api_manager.set_logger(self.logger)

    def log(self, message: str):
        if self.logger:
            self.logger.append(message)

    def get_timeline_buckets(self, is_archived, size, with_partners, with_stacked, visibility="", is_favorite=False, is_trashed=False, order="desc"):
        url = (
            f"/timeline/buckets"
            f"?isArchived={str(is_archived).lower()}"
            f"&size={size}"
            f"&withPartners={str(with_partners).lower()}"
            f"&withStacked={str(with_stacked).lower()}"
            f"&isFavorite={str(is_favorite).lower()}"
            f"&isTrashed={str(is_trashed).lower()}"
            f"&order={order}"
        )

        # Add visibility filter if specified
        if visibility:
            url += f"&visibility={visibility}"

        try:
            response = self.api_manager.get(url, expected_type=list)
            if not response:
                self.log("No buckets returned from API")
                return []

            validation_errors = []
            valid_buckets = []

            for bucket in response:
                error = self._validate_bucket(bucket)
                if error:
                    validation_errors.append(error)
                    continue
                valid_buckets.append(bucket)

            if validation_errors:
                self._log_validation_errors(validation_errors)

            return valid_buckets

        except Exception as e:
            self.log(f"Failed to fetch timeline buckets: {str(e)}")
            raise

    def _validate_bucket(self, bucket):
        """Validate a single bucket and return error message if invalid."""
        if not isinstance(bucket, dict):
            return "Invalid format"

        if 'timeBucket' not in bucket:
            return "Missing time"

        if 'count' not in bucket:
            return "Missing count"

        try:
            datetime.fromisoformat(bucket['timeBucket'].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return "Invalid time format"

        return None

    def _log_validation_errors(self, errors):
        """Log validation errors either verbosely or as a summary."""
        if not errors:
            return

        is_verbose = self.api_manager.debug.get('verbose_logging', False)
        error_count = len(errors)

        if is_verbose:
            for error in errors:
                self.log(f"Validation error: {error}")
        else:
            from collections import Counter
            error_types = Counter(errors)
            summary = ", ".join(f"{count} {error}" for error, count in error_types.items())
            self.log(f"Filtered {error_count} invalid buckets: {summary}")

    def get_timeline_bucket_assets(self, time_bucket, is_archived, size, with_partners, with_stacked, visibility="", is_favorite=False, is_trashed=False, order="desc"):
        if self.stop_flag():
            self.log("Fetch canceled by user.")
            return []

        url = (
            f"/timeline/bucket"
            f"?isArchived={str(is_archived).lower()}"
            f"&size={size}"
            f"&withPartners={str(with_partners).lower()}"
            f"&withStacked={str(with_stacked).lower()}"
            f"&timeBucket={time_bucket}"
            f"&isFavorite={str(is_favorite).lower()}"
            f"&isTrashed={str(is_trashed).lower()}"
            f"&order={order}"
        )

        # Add visibility filter if specified
        if visibility:
            url += f"&visibility={visibility}"

        try:
            response = self.api_manager.get(url, expected_type=dict)
            if not response or 'id' not in response:
                self.log("Invalid response format from timeline bucket API")
                return []

            # Convert parallel arrays format to array of objects
            ids = response.get('id', [])
            return [{'id': asset_id} for asset_id in ids]

        except Exception as e:
            self.log(f"Failed to fetch bucket assets: {str(e)}")
            raise

    def prepare_archive(self, asset_ids, archive_size_bytes):
        if not asset_ids:
            self.log("No assets provided for archive preparation")
            return {"totalSize": 0}

        payload = {
            "assetIds": asset_ids,
            "archiveSize": archive_size_bytes
        }
        try:
            response = self.api_manager.post("/download/info", json_data=payload, expected_type=dict)
            if not response or not isinstance(response.get('totalSize'), (int, float)):
                self.log("Invalid response format from prepare archive API")
                return {"totalSize": 0}
            return response
        except Exception as e:
            self.log(f"Failed to prepare archive: {str(e)}")
            raise

    def download_archive(self, asset_ids, bucket_name, total_size, current_download_progress_bar):
        if not asset_ids:
            self.log("No assets provided for download")
            return

        archive_path = os.path.join(self.output_dir, f"{bucket_name}.zip")
        try:
            os.makedirs(self.output_dir, exist_ok=True)

            # Skip if the file already exists and size matches (±1KB tolerance)
            if os.path.exists(archive_path):
                existing_size = os.path.getsize(archive_path)
                if abs(existing_size - total_size) <= 1024:
                    self.log(f"Archive '{bucket_name}.zip' exists. Skipping download.")
                    return

            self.log(f"Downloading archive: {bucket_name}.zip")
            payload = {"assetIds": asset_ids}
            try:
                response = self.api_manager.post("/download/archive", json_data=payload, stream=True, expected_type=None)
                if not response or not response.ok:
                    self.log(f"Failed to start download for {bucket_name}.zip: {response.status_code if response else 'No response'}")
                    return

                current_download_progress_bar.setValue(0)
                current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 0%")
                current_download_progress_bar.show()

                downloaded_size = 0
                start_time = time.time()
                last_logged_progress = 0

                with open(archive_path, "wb") as archive_file:
                    for chunk in response.iter_content(chunk_size=131072):  # 128KB chunk size for optimal network/memory balance
                        if self.stop_flag():
                            self.log("Download stopped by user.")
                            break

                        if chunk:
                            archive_file.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size:
                                progress = int((downloaded_size / total_size) * 100)
                                current_download_progress_bar.setValue(progress)
                                current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - {progress}%")

                                # Log every 1% progress change
                                if progress >= last_logged_progress + 1:
                                    last_logged_progress = progress
                                    self.log_download_progress(downloaded_size, start_time)
                            QApplication.processEvents()

                # Verify downloaded file size
                if os.path.exists(archive_path):
                    final_size = os.path.getsize(archive_path)
                    if abs(final_size - total_size) > 1024:  # 1KB tolerance
                        self.log(f"Warning: Downloaded file size ({final_size}) doesn't match expected size ({total_size})")
                        return

                if not self.stop_flag():
                    current_download_progress_bar.setValue(100)
                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 100%")
                    self.log(f"Archive downloaded: {bucket_name}.zip")
                    return

            except Exception as e:
                self.log(f"Error during download of {bucket_name}.zip: {str(e)}")
                # Clean up partial download
                if os.path.exists(archive_path):
                    os.remove(archive_path)
                return

        except Exception as e:
            self.log(f"Error setting up download for {bucket_name}.zip: {str(e)}")
            return

        return

    def log_download_progress(self, downloaded_size, start_time):
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            speed_mb = (downloaded_size / elapsed_time) / (1024 ** 2)
            self.log(f"Downloaded: {self.format_size(downloaded_size)}, Speed: {speed_mb:.2f} MB/s")

    @staticmethod
    def format_size(bytes_size):
        """Formats size in bytes to a human-readable format (GB and MB)."""
        if bytes_size >= 1024 ** 3:  # Size in GB
            gb_size = bytes_size / (1024 ** 3)
            return f"{gb_size:.2f} GB ({gb_size * 1024:.2f} MB)"
        elif bytes_size >= 1024 ** 2:  # Size in MB
            mb_size = bytes_size / (1024 ** 2)
            return f"0.00 GB ({mb_size:.2f} MB)"
        else:  # Size in KB
            kb_size = bytes_size / 1024
            return f"0.00 GB (0.00 MB) ({kb_size:.2f} KB)"

    @staticmethod
    def format_time_bucket(time_bucket, format="MONTH"):
        date_obj = datetime.fromisoformat(time_bucket.replace("Z", "+00:00"))

        if format.upper() == "DAY":
            return date_obj.strftime("%d.%m.%Y")
        else:
            return date_obj.strftime("%B_%Y")

    @staticmethod
    def calculate_file_checksum(file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()