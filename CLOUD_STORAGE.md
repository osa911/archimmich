# Cloud Storage Integration for ArchImmich

## Overview

ArchImmich now supports exporting archives directly to cloud storage providers, making it easy to backup your photo collections to remote storage services. This feature is designed with enterprise-grade security and reliability in mind.

## Supported Cloud Storage Providers

### WebDAV

- **Nextcloud/ownCloud**: Self-hosted cloud storage solutions
- **Synology/QNAP**: NAS devices with WebDAV support
- **Generic WebDAV**: Any WebDAV-compatible server
- **Authentication**: Basic Auth and Digest Auth support
- **Features**: Directory creation, file upload with progress tracking, integrity verification

### S3-Compatible Storage

- **Amazon S3**: Direct AWS S3 integration
- **MinIO**: Self-hosted S3-compatible storage
- **DigitalOcean Spaces**: Cloud object storage
- **Wasabi**: Hot cloud storage
- **Backblaze B2**: Cloud storage service
- **Other S3-compatible services**: Any service with S3 API compatibility
- **Features**: Multipart uploads for large files, streaming uploads, progress tracking

## Security Features

### Credential Encryption

- All cloud storage credentials are encrypted using AES-256 encryption
- Encryption keys are stored securely with restrictive file permissions
- Credentials are decrypted only when needed for operations

### Secure Storage

- Configuration files are stored in the user's application data directory
- File permissions are set to prevent unauthorized access
- No credentials are stored in plain text

## User Interface

### Cloud Storage Configuration

1. **Access**: Available in the export sidebar under "Cloud Storage"
2. **Destination Selection**: Choose between "Local Export" and "Cloud Export"
3. **Provider Configuration**: Click "Configure" to set up cloud storage providers
4. **Connection Testing**: Test connections before saving configurations

### Configuration Dialog

- **Professional UI**: Clean, intuitive interface for setting up cloud storage
- **Connection Testing**: Real-time connection validation
- **Help Text**: Built-in guidance for different providers
- **Error Handling**: Clear error messages and recovery suggestions

## Technical Implementation

### Architecture

```
ExportComponent
├── CloudStorageDialog (Configuration UI)
├── CloudStorageSettings (Credential Management)
├── CloudStorageManager (Core Operations)
└── ExportManager (Integration with existing export flow)
```

### Key Components

#### CloudStorageManager

- Handles all cloud storage operations
- Supports WebDAV and S3-compatible services
- Implements retry logic and error handling
- Provides progress tracking for uploads

#### CloudStorageSettings

- Manages encrypted credential storage
- Handles configuration persistence
- Provides secure credential retrieval

#### CloudStorageDialog

- Professional configuration interface
- Real-time connection testing
- Comprehensive error handling

### Integration with Existing Export Flow

- Seamlessly integrates with current export functionality
- Maintains all existing features (pause/resume, progress tracking)
- Adds cloud upload capability without breaking existing workflows

## Usage Instructions

### Setting Up Cloud Storage

1. **Access Configuration**:

   - In the Timeline tab, switch to "Cloud Export" mode
   - Click the "+" button to add a new cloud storage configuration

2. **WebDAV Configuration**:

   - **Display Name**: Give your configuration a friendly name (e.g., "My Nextcloud")
   - **Server URL**: Enter your WebDAV server URL
     - Nextcloud: `https://your-nextcloud.com/remote.php/dav/files/username/`
     - ownCloud: `https://your-owncloud.com/remote.php/dav/files/username/`
   - **Username**: Your server username
   - **Password**: Your password or app password (recommended for Nextcloud)
   - **Authentication**: Choose Basic or Digest authentication
   - **Remote Directory**: Optional directory path on the server

3. **S3 Configuration**:

   - **Display Name**: Give your configuration a friendly name (e.g., "AWS S3 Backup")
   - **Endpoint URL**: S3 endpoint (leave empty for AWS S3, or specify for other providers)
   - **Access Key**: Your S3 access key ID
   - **Secret Key**: Your S3 secret access key
   - **Bucket Name**: The bucket where files will be uploaded
   - **Region**: AWS region (e.g., us-east-1)
   - **Remote Prefix**: Optional prefix/folder path in the bucket

4. **Test Connection**:

   - Click "Test Connection" to verify your settings
   - Green checkmark indicates successful connection

5. **Save Configuration**:
   - Click "Save" to store your settings
   - Configuration is encrypted and stored securely

### Exporting to Cloud Storage

1. **Select Cloud Export**:

   - Choose "Cloud Export" in the export destination options
   - Select your configured cloud provider from the dropdown

2. **Configure Export**:

   - Set your filters and archive size as usual
   - Select the items you want to export

3. **Start Export**:
   - Click "Export" to begin the process
   - Monitor progress in the progress bars
   - Upload progress is shown in real-time

## Error Handling

### Connection Issues

- **Authentication Errors**: Clear messages for wrong credentials
- **Network Issues**: Timeout and connection error handling
- **Server Errors**: Detailed error messages with suggested actions

### Upload Issues

- **File Integrity**: Automatic verification of uploaded files
- **Progress Tracking**: Real-time upload progress with speed indicators
- **Error Recovery**: Clear error messages with recovery suggestions

## Security Considerations

### Credential Protection

- All passwords and API keys are encrypted at rest
- Encryption keys are stored with restrictive permissions
- No credentials are transmitted or stored in plain text

### Network Security

- All connections use HTTPS/TLS encryption
- Certificate validation is performed
- No credentials are logged or exposed

### Access Control

- Configuration files are stored in user-specific directories
- File permissions prevent unauthorized access
- Each user's configurations are isolated

## Troubleshooting

### Common Issues

#### WebDAV Connection Failed

- **Check URL**: Ensure the WebDAV URL is correct and accessible
- **Verify Credentials**: Double-check username and password
- **Authentication Type**: Try switching between Basic and Digest auth
- **Network**: Ensure your network allows WebDAV connections

#### Upload Failures

- **File Size**: Check if your server has file size limits
- **Permissions**: Verify you have write permissions to the target directory
- **Storage Space**: Ensure sufficient space is available on the server
- **Network Stability**: Check for network interruptions during upload

#### Configuration Issues

- **App Passwords**: For Nextcloud, use app passwords instead of your main password
- **Directory Paths**: Use forward slashes (/) in directory paths
- **URL Format**: Ensure URLs end with a trailing slash

### Getting Help

- Check the application logs for detailed error messages
- Verify your cloud storage provider's documentation
- Test connections using the built-in connection tester

## Future Enhancements

### Planned Features

- **Resume Uploads**: Resume interrupted uploads for all storage types
- **Multiple Providers**: Upload to multiple cloud storage providers simultaneously
- **Sync Options**: Two-way synchronization capabilities
- **Advanced Security**: OAuth2 support and additional authentication methods
- **Google Drive/OneDrive**: Support for popular consumer cloud services

### Performance Improvements

- **Parallel Uploads**: Upload multiple files simultaneously
- **Compression**: Optional compression before upload
- **Delta Sync**: Only upload changed files
- **Bandwidth Management**: Configurable upload speed limits

## Technical Requirements

### Dependencies

- `requests`: HTTP client for WebDAV operations
- `boto3`: AWS SDK for S3-compatible storage operations
- `cryptography`: Encryption for credential storage
- `PyQt5`: UI components (already required)

### System Requirements

- Python 3.7+
- Network access to cloud storage providers
- Sufficient disk space for temporary files during upload

## Development

### Testing

- Comprehensive test suite for all cloud storage functionality
- Mock-based testing for external dependencies
- Integration tests for end-to-end workflows

### Code Quality

- Type hints for all functions
- Comprehensive error handling
- Professional logging and debugging
- Clean, maintainable code structure

## Support

For issues or questions regarding cloud storage functionality:

1. Check the troubleshooting section above
2. Review application logs for detailed error information
3. Test connections using the built-in connection tester
4. Verify your cloud storage provider's documentation

---

_This cloud storage integration is designed to provide enterprise-grade reliability and security while maintaining the ease of use that ArchImmich is known for._
