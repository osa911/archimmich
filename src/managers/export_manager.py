import os
import time
import hashlib
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from src.utils.helpers import Logger

class ExportManager:
    def __init__(self, api_manager, logger, output_dir, stop_flag_callback):
        """
        Args:
            api_manager (APIManager): Instance of APIManager for API calls.
            logger (Logger): Existing logger instance to use for logging.
            output_dir (str): Directory where the archives will be saved.
            stop_flag_callback (callable): A function that returns True if stop is requested.
        """
        self.api_manager = api_manager
        self.logger = logger
        self.output_dir = output_dir
        self.stop_flag = stop_flag_callback
        # Don't set logger on API manager here since it should already be set
        # Resume functionality
        self.resume_metadata_dir = os.path.join(output_dir, ".archimmich_resume")
        os.makedirs(self.resume_metadata_dir, exist_ok=True)
        self.range_support_cache = {}  # Cache Range header support per server

    def log(self, message: str):
        if self.logger:
            self.logger.append(message)

    def get_timeline_buckets(self, is_archived, with_partners, with_stacked, visibility="", is_favorite=False, is_trashed=False, order="desc"):
        url = (
            f"/timeline/buckets"
            f"?isArchived={str(is_archived).lower()}"
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

    def get_timeline_bucket_assets(self, time_bucket, is_archived, with_partners, with_stacked, visibility="", is_favorite=False, is_trashed=False, order="desc"):
        if self.stop_flag():
            self.log("Fetch canceled by user.")
            return []

        url = (
            f"/timeline/bucket"
            f"?isArchived={str(is_archived).lower()}"
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

    def get_resume_metadata_path(self, archive_name):
        """Get path for resume metadata file."""
        return os.path.join(self.resume_metadata_dir, f"{archive_name}.resume.json")

    def save_resume_metadata(self, archive_name, asset_ids, total_size, downloaded_size):
        """Save resume metadata for partial download."""
        metadata = {
            "archive_name": archive_name,
            "asset_ids": asset_ids,
            "total_size": total_size,
            "downloaded_size": downloaded_size,
            "timestamp": time.time(),
            "partial_file_path": os.path.join(self.output_dir, f"{archive_name}.zip.partial")
        }
        metadata_path = self.get_resume_metadata_path(archive_name)
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            self.log(f"Failed to save resume metadata: {str(e)}")
            return False

    def load_resume_metadata(self, archive_name):
        """Load resume metadata for partial download."""
        metadata_path = self.get_resume_metadata_path(archive_name)
        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Verify partial file still exists
            partial_file = metadata.get('partial_file_path')
            if not partial_file or not os.path.exists(partial_file):
                # Clean up stale metadata
                os.remove(metadata_path)
                return None

            return metadata
        except Exception as e:
            self.log(f"Failed to load resume metadata: {str(e)}")
            return None

    def cleanup_resume_metadata(self, archive_name):
        """Clean up resume metadata after successful download."""
        metadata_path = self.get_resume_metadata_path(archive_name)
        if os.path.exists(metadata_path):
            try:
                os.remove(metadata_path)
            except Exception as e:
                self.log(f"Failed to cleanup resume metadata: {str(e)}")

    def can_resume_download(self, archive_name, asset_ids, total_size):
        """Check if download can be resumed."""
        metadata = self.load_resume_metadata(archive_name)
        if not metadata:
            return False, 0

        # Verify the download parameters match
        if (metadata.get('asset_ids') != asset_ids or
            metadata.get('total_size') != total_size):
            self.log(f"Resume metadata mismatch for {archive_name}, starting fresh download")
            self.cleanup_resume_metadata(archive_name)
            return False, 0

        downloaded_size = metadata.get('downloaded_size', 0)
        if downloaded_size >= total_size:
            self.log(f"Download already complete for {archive_name}")
            return False, 0

        return True, downloaded_size

    def check_existing_archives(self, archive_names):
        """Check which archives already exist in the output directory."""
        existing_files = []
        missing_files = []

        for archive_name in archive_names:
            archive_path = os.path.join(self.output_dir, f"{archive_name}.zip")
            if os.path.exists(archive_path):
                file_size = os.path.getsize(archive_path)
                existing_files.append({
                    'name': f"{archive_name}.zip",
                    'path': archive_path,
                    'size': file_size,
                    'size_formatted': self.format_size(file_size)
                })
            else:
                missing_files.append(f"{archive_name}.zip")

        # Log summary
        if existing_files:
            self.log(f"Found {len(existing_files)} existing archive(s) in output directory:")
            for file_info in existing_files:
                self.log(f"  ✓ {file_info['name']} ({file_info['size_formatted']})")

        if missing_files:
            self.log(f"{len(missing_files)} archive(s) will be downloaded:")
            for filename in missing_files:
                self.log(f"  • {filename}")

        return existing_files, missing_files

    def download_archive(self, asset_ids, bucket_name, total_size, current_download_progress_bar):
        if not asset_ids:
            self.log("No assets provided for download")
            return

        archive_path = os.path.join(self.output_dir, f"{bucket_name}.zip")
        partial_archive_path = f"{archive_path}.partial"

        try:
            os.makedirs(self.output_dir, exist_ok=True)

            # Skip if the file already exists and size matches with smart tolerance
            if os.path.exists(archive_path):
                existing_size = os.path.getsize(archive_path)

                # Calculate smart tolerance: minimum of 1KB or 0.1% of file size
                min_tolerance = 1024  # 1KB minimum
                percentage_tolerance = max(min_tolerance, int(total_size * 0.001))  # 0.1% of file size

                size_difference = abs(existing_size - total_size)

                if size_difference <= percentage_tolerance:
                    self.log(f"Archive '{bucket_name}.zip' already exists ({self.format_size(existing_size)}). Skipping download.")
                    return "completed"
                else:
                    # File exists but size doesn't match - could be corrupted or different content
                    self.log(f"Archive '{bucket_name}.zip' exists but size mismatch:")
                    self.log(f"  Existing: {self.format_size(existing_size)} ({existing_size:,} bytes)")
                    self.log(f"  Expected: {self.format_size(total_size)} ({total_size:,} bytes)")
                    self.log(f"  Difference: {self.format_size(size_difference)} ({size_difference:,} bytes)")
                    self.log(f"  Tolerance: {self.format_size(percentage_tolerance)} ({percentage_tolerance:,} bytes)")
                    self.log(f"File will be re-downloaded to ensure data integrity.")

            # Check for resume capability
            can_resume, existing_bytes = self.can_resume_download(bucket_name, asset_ids, total_size)

            # Check if server supports Range headers
            server_url = getattr(self.api_manager, 'server_url', 'unknown')
            server_supports_range = self.check_range_header_support(server_url)

            if can_resume:
                if not server_supports_range:
                    self.log(f"Resume attempted for {bucket_name}.zip but server doesn't support Range headers.")
                    self.log(f"Will start fresh download to avoid corruption. Your previous progress was: {self.format_size(existing_bytes)}")
                    downloaded_size = 0
                    file_mode = "wb"
                    headers = {}
                    # Clean any existing partial file
                    if os.path.exists(partial_archive_path):
                        os.remove(partial_archive_path)
                else:
                    self.log(f"Resuming download for {bucket_name}.zip from {self.format_size(existing_bytes)} ({existing_bytes} bytes)")
                    downloaded_size = existing_bytes
                    file_mode = "ab"  # Append mode for resume
                    headers = {"Range": f"bytes={existing_bytes}-"}
            else:
                self.log(f"Starting fresh download: {bucket_name}.zip")
                downloaded_size = 0
                file_mode = "wb"  # Write mode for new download
                headers = {}
                # Clean any existing partial file
                if os.path.exists(partial_archive_path):
                    os.remove(partial_archive_path)

            payload = {"assetIds": asset_ids}
            try:
                response = self.api_manager.post(
                    "/download/archive",
                    json_data=payload,
                    stream=True,
                    expected_type=None,
                    headers=headers
                )
                if not response or not response.ok:
                    if response and response.status_code == 416:  # Range not satisfiable
                        self.log(f"Resume not supported by server for {bucket_name}.zip, starting fresh")
                        # Retry without range header
                        if os.path.exists(partial_archive_path):
                            os.remove(partial_archive_path)
                        self.cleanup_resume_metadata(bucket_name)
                        return self.download_archive(asset_ids, bucket_name, total_size, current_download_progress_bar)
                    else:
                        self.log(f"Failed to start download for {bucket_name}.zip: {response.status_code if response else 'No response'}")
                        return "error"

                # Check if server actually honored the Range request
                actual_resume = False
                range_not_supported = False
                original_resume_bytes = existing_bytes  # Preserve original progress

                if can_resume and headers.get("Range"):
                    content_range = response.headers.get('Content-Range')
                    content_length = response.headers.get('Content-Length')

                    self.log(f"Range request debug: Content-Range='{content_range}', Content-Length='{content_length}'")

                    if content_range:
                        # Server honored the range request
                        actual_resume = True
                        self.log(f"Server honored Range request: {content_range}")
                    elif content_length and int(content_length) == (total_size - existing_bytes):
                        # Server sent partial content based on length
                        actual_resume = True
                        self.log(f"Server sent partial content: {content_length} bytes (expected {total_size - existing_bytes})")
                    else:
                        # Server ignored Range request and sent full content
                        range_not_supported = True

                        # Cache that this server doesn't support Range headers
                        self.set_range_header_support(server_url, False)

                        self.log(f"WARNING: Server doesn't support Range headers! Received {content_length} bytes, expected {total_size - existing_bytes}")
                        self.log(f"Your progress: {self.format_size(existing_bytes)} ({existing_bytes:,} bytes) will be preserved.")
                        self.log("Continuing with fresh download to avoid corruption...")

                        # Close current response and start fresh
                        response.close()

                        # Start fresh download but preserve original resume metadata
                        downloaded_size = 0
                        file_mode = "wb"

                        # Remove any existing partial file since we're starting fresh
                        if os.path.exists(partial_archive_path):
                            os.remove(partial_archive_path)

                        response = self.api_manager.post(
                            "/download/archive",
                            json_data=payload,
                            stream=True,
                            expected_type=None,
                            headers={}
                        )
                        actual_resume = False

                # Track bytes downloaded in this session vs total bytes written to file
                session_downloaded = 0  # Bytes downloaded in this session
                total_bytes_written = downloaded_size  # Total bytes written to file (including existing)

                # Update progress bar for resume
                if actual_resume and downloaded_size > 0:
                    initial_progress = int((downloaded_size / total_size) * 100) if total_size else 0
                    current_download_progress_bar.setValue(initial_progress)
                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - {initial_progress}% (Resumed: +{self.format_size(session_downloaded)})")
                    self.log(f"Resume progress: {initial_progress}% ({self.format_size(downloaded_size)}/{self.format_size(total_size)})")
                else:
                    current_download_progress_bar.setValue(0)
                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 0%")

                current_download_progress_bar.show()

                start_time = time.time()
                last_logged_progress = int((total_bytes_written / total_size) * 100) if total_size else 0
                last_save_time = time.time()
                save_interval = 5.0  # Save resume metadata every 5 seconds

                with open(partial_archive_path, file_mode) as archive_file:
                    for chunk in response.iter_content(chunk_size=131072):  # 128KB chunk size
                        if self.stop_flag():
                            # Special handling for range-not-supported case
                            if range_not_supported:
                                # Preserve original resume metadata instead of overwriting with fresh download progress
                                if self.save_resume_metadata(bucket_name, asset_ids, total_size, original_resume_bytes):
                                    self.log(f"Download paused. Original resume data preserved for {bucket_name}.zip ({self.format_size(original_resume_bytes)}/{self.format_size(total_size)})")
                                    self.log(f"Note: Server doesn't support Range headers. Next resume will restart from 0% to avoid corruption.")
                                else:
                                    self.log(f"Download stopped. Failed to preserve resume data for {bucket_name}.zip")
                            else:
                                # Normal case - save current progress
                                if self.save_resume_metadata(bucket_name, asset_ids, total_size, total_bytes_written):
                                    self.log(f"Download paused. Resume data saved for {bucket_name}.zip ({self.format_size(total_bytes_written)}/{self.format_size(total_size)})")
                                else:
                                    self.log(f"Download stopped. Failed to save resume data for {bucket_name}.zip")
                            return "paused"

                        if chunk:
                            archive_file.write(chunk)
                            session_downloaded += len(chunk)
                            total_bytes_written += len(chunk)

                            if total_size:
                                progress = int((total_bytes_written / total_size) * 100)
                                # Ensure progress never exceeds 100%
                                progress = min(progress, 100)
                                current_download_progress_bar.setValue(progress)

                                if actual_resume:
                                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - {progress}% (Resumed: +{self.format_size(session_downloaded)})")
                                else:
                                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - {progress}%")

                                # Log progress every 1%
                                if progress >= last_logged_progress + 1:
                                    last_logged_progress = progress
                                    if actual_resume:
                                        self.log(f"Download progress: {progress}% (Total: {self.format_size(total_bytes_written)}, Session: +{self.format_size(session_downloaded)})")
                                    else:
                                        self.log(f"Download progress: {progress}% ({self.format_size(total_bytes_written)})")

                                # Save resume metadata periodically (but not if range not supported and we're in fresh download)
                                current_time = time.time()
                                if current_time - last_save_time >= save_interval:
                                    if not range_not_supported:
                                        # Only save current progress if Range headers work
                                        self.save_resume_metadata(bucket_name, asset_ids, total_size, total_bytes_written)
                                    # Don't overwrite original progress when range not supported
                                    last_save_time = current_time

                            QApplication.processEvents()

                # Download completed successfully
                if not self.stop_flag():
                    current_download_progress_bar.setValue(100)
                    current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 100%")

                    # Move partial file to final location
                    if os.path.exists(partial_archive_path):
                        if os.path.exists(archive_path):
                            os.remove(archive_path)
                        os.rename(partial_archive_path, archive_path)

                    # Clean up resume metadata
                    self.cleanup_resume_metadata(bucket_name)

                    final_size = os.path.getsize(archive_path)
                    self.log(f"Download completed: {bucket_name}.zip ({self.format_size(final_size)})")

                    if actual_resume:
                        self.log(f"Resume session downloaded: {self.format_size(session_downloaded)} additional bytes")

                    # Verify file size matches expected with smart tolerance
                    size_difference = abs(final_size - total_size)

                    # Calculate smart tolerance: minimum 1KB or 0.1% of file size, whichever is larger
                    min_tolerance = 1024  # 1KB minimum
                    percentage_tolerance = max(min_tolerance, int(total_size * 0.001))  # 0.1% of file size

                    if size_difference > percentage_tolerance:
                        self.log(f"WARNING: File size mismatch! Expected: {self.format_size(total_size)} ({total_size:,} bytes), Got: {self.format_size(final_size)} ({final_size:,} bytes)")
                        self.log(f"Difference: {self.format_size(size_difference)} ({size_difference:,} bytes), Tolerance: {self.format_size(percentage_tolerance)} ({percentage_tolerance:,} bytes)")

                    return "completed"

            except Exception as e:
                self.log(f"Error during download of {bucket_name}.zip: {str(e)}")
                # Don't clean up partial download on error - allow resume
                return "error"

        except Exception as e:
            self.log(f"Error setting up download for {bucket_name}.zip: {str(e)}")
            return "error"

        return "unknown"

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
    def format_time_bucket(time_bucket):
        date_obj = datetime.fromisoformat(time_bucket.replace("Z", "+00:00"))
        return date_obj.strftime("%B_%Y")

    @staticmethod
    def calculate_file_checksum(file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def check_range_header_support(self, server_url):
        """Check if server supports Range headers (cached)."""
        if server_url in self.range_support_cache:
            return self.range_support_cache[server_url]
        # Default to True - we'll detect and cache when it fails
        return True

    def set_range_header_support(self, server_url, supports_range):
        """Cache Range header support status for server."""
        self.range_support_cache[server_url] = supports_range
        if not supports_range:
            self.log(f"Note: Server {server_url} doesn't support Range headers - resume functionality limited")