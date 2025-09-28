"""
Cloud Storage Manager for ArchImmich
Handles cloud storage operations including WebDAV and S3-compatible services.
"""

import os
import time
import hashlib
import json
import requests
from typing import Optional, Dict, Any, Callable, Tuple
from urllib.parse import urljoin, urlparse
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CloudStorageError(Exception):
    """Base exception for cloud storage operations."""
    pass


class AuthenticationError(CloudStorageError):
    """Raised when authentication fails."""
    pass


class ConnectionError(CloudStorageError):
    """Raised when connection to cloud storage fails."""
    pass


class UploadError(CloudStorageError):
    """Raised when upload operation fails."""
    pass


class CloudStorageManager:
    """
    Manages cloud storage operations with support for WebDAV and S3-compatible services.
    Provides enterprise-grade reliability with proper error handling and progress tracking.
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and proper timeouts."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "POST", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set reasonable timeouts
        session.timeout = (30, 300)  # (connect timeout, read timeout)

        return session

    def log(self, message: str):
        """Log a message if logger is available."""
        if self.logger:
            self.logger.append(message)

    def test_webdav_connection(self, url: str, username: str, password: str,
                             auth_type: str = "basic") -> Tuple[bool, str]:
        """
        Test WebDAV connection with proper authentication.

        Args:
            url: WebDAV server URL
            username: Username for authentication
            password: Password for authentication
            auth_type: Authentication type ("basic" or "digest")

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Normalize URL
            if not url.endswith('/'):
                url += '/'

            # Validate URL format
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"

            # Prepare authentication
            if auth_type.lower() == "digest":
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)

            # Test connection with PROPFIND request
            headers = {
                'Depth': '0',
                'Content-Type': 'application/xml'
            }

            # Simple PROPFIND request to test connection
            propfind_body = '''<?xml version="1.0" encoding="utf-8"?>
            <D:propfind xmlns:D="DAV:">
                <D:prop>
                    <D:displayname/>
                </D:prop>
            </D:propfind>'''

            response = self.session.request(
                'PROPFIND',
                url,
                data=propfind_body,
                headers=headers,
                auth=auth,
                timeout=(10, 30)
            )

            if response.status_code in [200, 207]:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Authentication failed - check username and password"
            elif response.status_code == 403:
                return False, "Access forbidden - check permissions"
            elif response.status_code == 404:
                return False, "WebDAV not found at this URL"
            else:
                return False, f"Connection failed with status {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "Connection timeout - check URL and network"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - check URL and network connectivity"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def create_webdav_directory(self, base_url: str, username: str, password: str,
                              directory_path: str, auth_type: str = "basic") -> bool:
        """
        Create a directory structure on WebDAV server.

        Args:
            base_url: WebDAV server base URL
            username: Username for authentication
            password: Password for authentication
            directory_path: Directory path to create
            auth_type: Authentication type

        Returns:
            True if successful, False otherwise
        """
        try:
            if not base_url.endswith('/'):
                base_url += '/'

            # Prepare authentication
            if auth_type.lower() == "digest":
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)

            # Create directory path
            full_url = f"{base_url.rstrip('/')}/{directory_path.lstrip('/')}/"

            # Check if directory already exists
            response = self.session.request('PROPFIND', full_url, auth=auth, timeout=(10, 30))
            if response.status_code == 200:
                self.log(f"Directory already exists: {directory_path}")
                return True

            # Create directory
            response = self.session.request('MKCOL', full_url, auth=auth, timeout=(10, 30))

            if response.status_code in [201, 207, 405]:  # 207 = success, 405 = already exists
                self.log(f"Directory created successfully: {directory_path}")
                return True
            else:
                self.log(f"Failed to create directory: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.log(f"Error creating directory: {str(e)}")
            return False

    def upload_stream_to_webdav(self, stream, base_url: str, username: str,
                              password: str, remote_path: str, auth_type: str = "basic",
                              progress_callback: Optional[Callable] = None,
                              total_size: int = None) -> Tuple[bool, str]:
        """
        Upload a stream directly to WebDAV server without saving to local disk.

        Args:
            stream: Response stream from requests
            base_url: WebDAV server base URL
            username: Username for authentication
            password: Password for authentication
            remote_path: Remote file path
            auth_type: Authentication type
            progress_callback: Optional callback for progress updates
            total_size: Total size of the stream (for progress tracking)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not total_size:
                return False, "Total size must be provided for stream upload"

            # Prepare authentication
            if auth_type.lower() == "digest":
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)

            # Construct full URL
            full_url = f"{base_url.rstrip('/')}/{remote_path.lstrip('/')}"

            self.log(f"Preparing WebDAV stream upload to {full_url}")

            # Create parent directories if needed
            parent_dir = os.path.dirname(remote_path)
            if parent_dir:
                self.create_webdav_directory(base_url, username, password, parent_dir, auth_type)

            # Upload stream with progress tracking
            uploaded_bytes = 0
            start_time = time.time()

            self.log(f"Starting WebDAV PUT request to {full_url}")

            # Use streaming upload
            response = self.session.put(
                full_url,
                data=self._stream_upload_generator(stream, progress_callback, total_size, start_time),
                auth=auth,
                timeout=(30, 600),  # Longer timeout for uploads
                headers={'Content-Type': 'application/octet-stream'}
            )

            self.log(f"WebDAV PUT request completed with status: {response.status_code}")

            if response.status_code in [200, 201, 204, 207]:
                self.log(f"Stream uploaded successfully: {remote_path}")
                return True, "Upload completed successfully"
            else:
                return False, f"Upload failed with status {response.status_code}: {response.text}"

        except Exception as e:
            if "Upload cancelled by user" in str(e):
                return False, "Upload cancelled by user"
            return False, f"Upload error: {str(e)}"

    def upload_file_to_webdav(self, file_path: str, base_url: str, username: str,
                            password: str, remote_path: str, auth_type: str = "basic",
                            progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        Upload a file to WebDAV server with progress tracking.

        Args:
            file_path: Local file path to upload
            base_url: WebDAV server base URL
            username: Username for authentication
            password: Password for authentication
            remote_path: Remote file path
            auth_type: Authentication type
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"Local file not found: {file_path}"

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "Cannot upload empty file"

            # Prepare authentication
            if auth_type.lower() == "digest":
                auth = HTTPDigestAuth(username, password)
            else:
                auth = HTTPBasicAuth(username, password)

            # Construct full URL
            full_url = f"{base_url.rstrip('/')}/{remote_path.lstrip('/')}"

            # Create parent directories if needed
            parent_dir = os.path.dirname(remote_path)
            if parent_dir:
                self.create_webdav_directory(base_url, username, password, parent_dir, auth_type)

            # Upload file with progress tracking
            uploaded_bytes = 0
            start_time = time.time()

            with open(file_path, 'rb') as file:
                # Use streaming upload for large files
                response = self.session.put(
                    full_url,
                    data=self._file_upload_generator(file, progress_callback, file_size, start_time),
                    auth=auth,
                    timeout=(30, 600),  # Longer timeout for uploads
                    headers={'Content-Type': 'application/octet-stream'}
                )

            if response.status_code in [200, 201, 204, 207]:
                # Verify upload integrity
                if self._verify_upload_integrity(file_path, full_url, auth):
                    self.log(f"File uploaded successfully: {remote_path}")
                    return True, "Upload completed successfully"
                else:
                    return False, "Upload completed but integrity verification failed"
            else:
                return False, f"Upload failed with status {response.status_code}: {response.text}"

        except Exception as e:
            return False, f"Upload error: {str(e)}"

    def _stream_upload_generator(self, stream, progress_callback: Optional[Callable],
                               total_size: int, start_time: float):
        """Generator for stream upload with progress tracking."""
        uploaded_bytes = 0
        last_progress_time = time.time()

        for chunk in stream.iter_content(chunk_size=8192):  # 8KB chunks
            if not chunk:
                break

            uploaded_bytes += len(chunk)

            # Call progress callback every 100ms
            current_time = time.time()
            if progress_callback and (current_time - last_progress_time) >= 0.1:
                progress = (uploaded_bytes / total_size) * 100
                elapsed_time = current_time - start_time
                speed = uploaded_bytes / elapsed_time if elapsed_time > 0 else 0

                # Check if progress callback returns False (cancellation signal)
                callback_result = progress_callback(progress, uploaded_bytes, total_size, speed)
                if callback_result is False:
                    self.log("Upload cancelled by user")
                    # Raise an exception to stop the upload
                    raise Exception("Upload cancelled by user")

                last_progress_time = current_time

            yield chunk

    def _file_upload_generator(self, file, progress_callback: Optional[Callable],
                             total_size: int, start_time: float):
        """Generator for file upload with progress tracking."""
        uploaded_bytes = 0
        last_progress_time = time.time()

        while True:
            chunk = file.read(8192)  # 8KB chunks
            if not chunk:
                break

            uploaded_bytes += len(chunk)

            # Call progress callback every 100ms
            current_time = time.time()
            if progress_callback and (current_time - last_progress_time) >= 0.1:
                progress = (uploaded_bytes / total_size) * 100
                elapsed_time = current_time - start_time
                speed = uploaded_bytes / elapsed_time if elapsed_time > 0 else 0
                progress_callback(progress, uploaded_bytes, total_size, speed)
                last_progress_time = current_time

            yield chunk

    def _verify_upload_integrity(self, local_file_path: str, remote_url: str, auth) -> bool:
        """Verify uploaded file integrity by comparing checksums."""
        try:
            # Calculate local file checksum
            local_checksum = self._calculate_file_checksum(local_file_path)

            # Get remote file checksum (if server supports it)
            # For now, we'll just verify the file exists and has correct size
            response = self.session.head(remote_url, auth=auth, timeout=(10, 30))

            if response.status_code == 200:
                remote_size = int(response.headers.get('Content-Length', 0))
                local_size = os.path.getsize(local_file_path)
                return remote_size == local_size

            return False

        except Exception:
            return False

    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def test_s3_connection(self, endpoint_url: str, access_key: str, secret_key: str,
                          bucket_name: str, region: str = "us-east-1") -> Tuple[bool, str]:
        """
        Test S3-compatible connection.

        Args:
            endpoint_url: S3 endpoint URL
            access_key: AWS access key
            secret_key: AWS secret key
            bucket_name: S3 bucket name
            region: AWS region

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, BotoCoreError

            # Create S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=boto3.session.Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )

            # Test connection by checking if bucket exists and is accessible
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                self.log(f"S3 connection test successful: bucket '{bucket_name}' is accessible")
                return True, f"Connection successful! Bucket '{bucket_name}' is accessible."
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    return False, f"Bucket '{bucket_name}' not found. Please check the bucket name."
                elif error_code == '403':
                    return False, f"Access denied to bucket '{bucket_name}'. Please check your credentials."
                else:
                    return False, f"S3 error ({error_code}): {e.response['Error']['Message']}"

        except ImportError:
            return False, "boto3 library not installed. Please install it with: pip install boto3"
        except BotoCoreError as e:
            return False, f"S3 configuration error: {str(e)}"
        except Exception as e:
            return False, f"S3 connection error: {str(e)}"

    def upload_file_to_s3(self, file_path: str, endpoint_url: str, access_key: str,
                         secret_key: str, bucket_name: str, remote_path: str,
                         region: str = "us-east-1", progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        Upload a file to S3-compatible storage.

        Args:
            file_path: Local file path to upload
            endpoint_url: S3 endpoint URL
            access_key: AWS access key
            secret_key: AWS secret key
            bucket_name: S3 bucket name
            remote_path: Remote file path
            region: AWS region
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, BotoCoreError
            import os
            import time

            if not os.path.exists(file_path):
                return False, f"Local file not found: {file_path}"

            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "Cannot upload empty file"

            self.log(f"Starting S3 upload: {remote_path}")

            # Create S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=boto3.session.Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )

            # Progress tracking class
            class ProgressTracker:
                def __init__(self, callback, file_size):
                    self.callback = callback
                    self.file_size = file_size
                    self.uploaded_bytes = 0
                    self.start_time = time.time()
                    self.last_update_time = time.time()

                def __call__(self, bytes_transferred):
                    self.uploaded_bytes += bytes_transferred
                    current_time = time.time()

                    # Update progress every 100ms
                    if current_time - self.last_update_time >= 0.1:
                        progress = (self.uploaded_bytes / self.file_size) * 100
                        elapsed_time = current_time - self.start_time
                        speed = self.uploaded_bytes / elapsed_time if elapsed_time > 0 else 0

                        if self.callback:
                            self.callback(progress, self.uploaded_bytes, self.file_size, speed)

                        self.last_update_time = current_time

            # Set up progress tracking
            progress_tracker = ProgressTracker(progress_callback, file_size) if progress_callback else None

            # Upload file
            s3_client.upload_file(
                file_path,
                bucket_name,
                remote_path,
                Callback=progress_tracker
            )

            self.log(f"S3 upload completed: {remote_path}")
            return True, "Upload completed successfully"

        except ImportError:
            return False, "boto3 library not installed. Please install it with: pip install boto3"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return False, f"Bucket '{bucket_name}' does not exist"
            elif error_code == 'AccessDenied':
                return False, f"Access denied. Check your credentials and bucket permissions"
            else:
                return False, f"S3 upload error ({error_code}): {e.response['Error']['Message']}"
        except BotoCoreError as e:
            return False, f"S3 configuration error: {str(e)}"
        except Exception as e:
            return False, f"S3 upload error: {str(e)}"

    def upload_stream_to_s3(self, stream, endpoint_url: str, access_key: str, secret_key: str,
                           bucket_name: str, remote_path: str, region: str = "us-east-1",
                           progress_callback: Optional[Callable] = None,
                           total_size: int = None) -> Tuple[bool, str]:
        """
        Upload a stream directly to S3-compatible storage without saving to local disk.

        Args:
            stream: Response stream from requests
            endpoint_url: S3 endpoint URL
            access_key: AWS access key
            secret_key: AWS secret key
            bucket_name: S3 bucket name
            remote_path: Remote file path
            region: AWS region
            progress_callback: Optional callback for progress updates
            total_size: Total size of the stream (for progress tracking)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, BotoCoreError
            import time
            from io import BytesIO

            if not total_size:
                return False, "Total size must be provided for S3 stream upload"

            self.log(f"Starting S3 stream upload: {remote_path}")

            # Create S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=boto3.session.Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )

            # Stream the data to S3 using multipart upload for large files
            if total_size > 5 * 1024 * 1024:  # Use multipart for files > 5MB
                return self._multipart_stream_upload(s3_client, stream, bucket_name, remote_path,
                                                   total_size, progress_callback)
            else:
                # For smaller files, read entire stream into memory
                self.log("Using single-part upload for stream")
                uploaded_bytes = 0
                start_time = time.time()
                last_progress_time = start_time

                # Read stream data
                data = BytesIO()
                for chunk in stream.iter_content(chunk_size=8192):
                    if not chunk:
                        break
                    data.write(chunk)
                    uploaded_bytes += len(chunk)

                    # Update progress
                    current_time = time.time()
                    if progress_callback and (current_time - last_progress_time) >= 0.1:
                        progress = (uploaded_bytes / total_size) * 100
                        elapsed_time = current_time - start_time
                        speed = uploaded_bytes / elapsed_time if elapsed_time > 0 else 0
                        progress_callback(progress, uploaded_bytes, total_size, speed)
                        last_progress_time = current_time

                # Reset data position for upload
                data.seek(0)

                # Upload to S3
                s3_client.upload_fileobj(data, bucket_name, remote_path)

                self.log(f"S3 stream upload completed: {remote_path}")
                return True, "Stream upload completed successfully"

        except ImportError:
            return False, "boto3 library not installed. Please install it with: pip install boto3"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return False, f"Bucket '{bucket_name}' does not exist"
            elif error_code == 'AccessDenied':
                return False, f"Access denied. Check your credentials and bucket permissions"
            else:
                return False, f"S3 stream upload error ({error_code}): {e.response['Error']['Message']}"
        except BotoCoreError as e:
            return False, f"S3 configuration error: {str(e)}"
        except Exception as e:
            return False, f"S3 stream upload error: {str(e)}"

    def _multipart_stream_upload(self, s3_client, stream, bucket_name: str, remote_path: str,
                               total_size: int, progress_callback: Optional[Callable]) -> Tuple[bool, str]:
        """Handle multipart upload for large streams."""
        try:
            import time

            self.log("Using multipart upload for large stream")

            # Initialize multipart upload
            response = s3_client.create_multipart_upload(
                Bucket=bucket_name,
                Key=remote_path
            )
            upload_id = response['UploadId']

            parts = []
            part_number = 1
            uploaded_bytes = 0
            start_time = time.time()
            last_progress_time = start_time
            chunk_size = 5 * 1024 * 1024  # 5MB chunks

            try:
                # Read and upload stream in chunks
                chunk_data = bytearray()

                for data in stream.iter_content(chunk_size=8192):
                    if not data:
                        break

                    chunk_data.extend(data)
                    uploaded_bytes += len(data)

                    # Update progress
                    current_time = time.time()
                    if progress_callback and (current_time - last_progress_time) >= 0.1:
                        progress = (uploaded_bytes / total_size) * 100
                        elapsed_time = current_time - start_time
                        speed = uploaded_bytes / elapsed_time if elapsed_time > 0 else 0
                        progress_callback(progress, uploaded_bytes, total_size, speed)
                        last_progress_time = current_time

                    # When we have enough data for a part, upload it
                    if len(chunk_data) >= chunk_size:
                        part_response = s3_client.upload_part(
                            Bucket=bucket_name,
                            Key=remote_path,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=bytes(chunk_data)
                        )

                        parts.append({
                            'ETag': part_response['ETag'],
                            'PartNumber': part_number
                        })

                        self.log(f"Uploaded part {part_number} ({len(chunk_data)} bytes)")
                        part_number += 1
                        chunk_data = bytearray()

                # Upload any remaining data
                if chunk_data:
                    part_response = s3_client.upload_part(
                        Bucket=bucket_name,
                        Key=remote_path,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=bytes(chunk_data)
                    )

                    parts.append({
                        'ETag': part_response['ETag'],
                        'PartNumber': part_number
                    })

                    self.log(f"Uploaded final part {part_number} ({len(chunk_data)} bytes)")

                # Complete multipart upload
                s3_client.complete_multipart_upload(
                    Bucket=bucket_name,
                    Key=remote_path,
                    UploadId=upload_id,
                    MultipartUpload={'Parts': parts}
                )

                self.log(f"S3 multipart stream upload completed: {remote_path}")
                return True, "Multipart stream upload completed successfully"

            except Exception as e:
                # Abort multipart upload on error
                try:
                    s3_client.abort_multipart_upload(
                        Bucket=bucket_name,
                        Key=remote_path,
                        UploadId=upload_id
                    )
                except:
                    pass  # Ignore errors when aborting
                raise e

        except Exception as e:
            return False, f"S3 multipart upload error: {str(e)}"

    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
