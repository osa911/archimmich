import os
import time
import hashlib
from datetime import datetime
from PyQt5.QtWidgets import QApplication

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
        self.logs = logs_widget
        self.output_dir = output_dir
        self.stop_flag = stop_flag_callback

    def log(self, message: str):
        if self.logs:
            self.logs.append(message)

    def get_timeline_buckets(self, is_archived, size, with_partners, with_stacked):
        url = (
            f"/timeline/buckets"
            f"?isArchived={str(is_archived).lower()}"
            f"&size={size}"
            f"&withPartners={str(with_partners).lower()}"
            f"&withStacked={str(with_stacked).lower()}"
        )
        response = self.api_manager.get(url)
        return response.json()

    def get_timeline_bucket_assets(self, time_bucket, is_archived, size, with_partners, with_stacked):
        url = (
            f"/timeline/bucket"
            f"?isArchived={str(is_archived).lower()}"
            f"&size={size}"
            f"&withPartners={str(with_partners).lower()}"
            f"&withStacked={str(with_stacked).lower()}"
            f"&timeBucket={time_bucket}"
        )
        if self.stop_flag():
            self.log("Fetch canceled by user.")
            return []
        response = self.api_manager.get(url)
        return response.json()

    def prepare_archive(self, asset_ids, archive_size_bytes):
        payload = {
            "assetIds": asset_ids,
            "archiveSize": archive_size_bytes
        }
        response = self.api_manager.post("/download/info", json_data=payload)
        return response.json()

    def download_archive(self, asset_ids, bucket_name, total_size, current_download_progress_bar):
        archive_path = os.path.join(self.output_dir, f"{bucket_name}.zip")
        os.makedirs(self.output_dir, exist_ok=True)

        # Skip if the file already exists and size matches (±1KB tolerance)
        if os.path.exists(archive_path):
            existing_size = os.path.getsize(archive_path)
            if abs(existing_size - total_size) <= 1024:
                self.log(f"Archive '{bucket_name}.zip' exists. Skipping download.")
                return

        self.log(f"Downloading archive: {bucket_name}.zip")
        payload = {"assetIds": asset_ids}
        response = self.api_manager.post("/download/archive", json_data=payload, stream=True)

        current_download_progress_bar.setValue(0)
        current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 0%")
        current_download_progress_bar.show()

        downloaded_size = 0
        start_time = time.time()

        with open(archive_path, "wb") as archive_file:
            for chunk in response.iter_content(chunk_size=8192):
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

                    # Log and update UI
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        speed_mb = (downloaded_size / elapsed_time) / (1024 ** 2)
                        self.log(f"Downloaded: {self.format_size(downloaded_size)}, Speed: {speed_mb:.2f} MB/s")
                    QApplication.processEvents()

        if not self.stop_flag():
            current_download_progress_bar.setValue(100)
            current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 100%")
            self.log(f"Archive downloaded: {bucket_name}.zip")

    @staticmethod
    def format_size(bytes_size):
        gb_size = bytes_size / (1024 ** 3)
        mb_size = bytes_size / (1024 ** 2)
        return f"{gb_size:.2f} GB ({mb_size:.2f} MB)"

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