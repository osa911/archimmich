# Changelog

All notable changes to this project will be documented in this file.

## [v0.3.0] - Cloud Storage Integration - 2025-09-28

### ☁️ **Export Directly to Cloud Storage**

Now you can export your Immich photos and albums directly to your cloud storage without using local disk space!

**Supported Cloud Providers:**

- **WebDAV Services**: Nextcloud, ownCloud, Synology, QNAP, and more
- **S3-Compatible Storage**: AWS S3, MinIO, DigitalOcean Spaces, Wasabi, Backblaze B2

### 🆕 **New Features**

#### **Cloud Export Mode**

- Switch to "Cloud Export" on the Timeline tab to upload directly to your cloud storage
- No more filling up your local disk with large export files
- Perfect for backing up huge photo collections

#### **Multiple Cloud Configurations**

- Save multiple cloud storage accounts and easily switch between them
- Give each configuration a friendly name (e.g., "Personal Nextcloud", "Work S3")
- Edit, rename, or delete saved configurations anytime

#### **Real-Time Progress**

- Watch your uploads progress with live speed indicators (MB/s)
- See exactly how much has been uploaded and time remaining
- Same smooth progress experience as local exports

#### **Secure & Easy Setup**

- Test your cloud connection before saving to make sure everything works
- All passwords and access keys are encrypted and stored securely
- Simple setup wizard guides you through configuration

### 🚀 **Getting Started**

1. **Go to Timeline tab** and click the cloud button to switch to Cloud Export
2. **Add your cloud storage** by clicking the "+" button and entering your details
3. **Test the connection** to make sure everything works
4. **Start exporting** - your files will upload directly to the cloud!

### 📱 **Perfect For**

- **Large photo libraries** that would fill up your computer
- **Regular backups** to multiple cloud services
- **Sharing exports** by uploading to shared cloud folders
- **Long-term archival** without local storage concerns

---

_For technical documentation, see [CLOUD_STORAGE.md](CLOUD_STORAGE.md)_

## [0.2.0] - 2025-08-03

### Added

- **Album Export Feature**:
  - Support for browsing and exporting albums
  - Search functionality to filter albums by name
  - Dual view modes: List and Grid (covers) view
  - Dynamic album cover size adjustment (75px to 350px)
  - Thumbnail caching for improved performance
  - Responsive grid layout with automatic reflow
  - Album cover hover effects showing full album names
- **Export Enhancements**:
  - Pause and resume support for album exports
  - Export path validation for albums tab
  - Prevention of tab switching during active exports
  - Clear feedback when no albums are found
  - Error messages displayed in UI for fetch failures

### Changed

- **UI Improvements**:
  - Added icons to buttons and labels
  - Better visual clarity and user experience

### Technical Improvements

- **Testing**:
  - Added comprehensive tests for album export features
  - Enhanced CI workflow with headless GUI testing support

## [0.1.0] - 2025-06-16

### Added

- **Smart File Checking**: Automatic detection and skipping of already downloaded files to prevent duplicates.
- **Export Protection**: Directory selection is disabled during active exports to prevent conflicts.
- **Auto-Stop on Logout**: Ongoing exports are safely stopped when user logs out.
- **Settings Dialog**: New "Settings" dialog accessible via Settings menu with debug options.
- **About Dialog**: New "About ArchImmich" dialog with version info and support links.
- **Advanced Export Options**:
  - Support for visibility filters (archive, timeline, hidden, locked).
  - Removed "Size" filter as server does not support it anymore.
  - Favorite and trashed asset filtering.
  - Add "Order ASC/DESC" option to sort assets.
- **Robust Error Handling**: Enhanced API error handling with detailed logging and user feedback.
- **Server Integration**: Display server version information on successful login.
- **Range Header Detection**: Smart detection of server Range header support with automatic fallback.

### Changed

- **Refactored Architecture**: Complete UI restructure with separate components for better maintainability.
- **Enhanced Logging**: Background logging with thread-based queue system for improved performance and saving logs to file per session.
- **Better Configuration Management**: Centralized settings with JSON-based storage and debug options.
- **Window Management**: Improved window dimensions, minimum size constraints, and responsive layout.
- **Config File**: The config file is stored as `config.json` in the user data directory for persistence across app updates
- **Settings Migration**: Settings are automatically migrated from old locations when upgrading

### Fixed

- **File Size Verification**: Improved tolerance for file size mismatches (0.1% tolerance or minimum 1KB).
- **Memory Management**: Better cleanup and resource management during logout operations.
- **Export Workflow**: Enhanced export finalization and state management.

### Technical Improvements

- **Comprehensive Testing**: Added extensive test coverage for all components and functionality.
- **Code Organization**: Separated business logic into dedicated method classes for better maintainability.
- **Build System**: Enhanced packaging scripts with version management across multiple files.
- **Documentation**: Improved inline documentation and code comments.
- **Error Recovery**: Better handling of network interruptions and server compatibility issues.

## [0.0.2] - 2024-12-23

### Added

- Persistent storage for server IP and API key, allowing automatic reuse after reopening the app.
- Improved `output_dir_label` persistence after fetching buckets.
- Enhanced stop button behavior to replace the export button dynamically.
- Clear separation of archive modes: "Month" and "Single Archive."

### Changed

- Refactored export logic for better clarity and performance.
- Optimized progress bar updates for smoother UI rendering.

### Fixed

- Fixed double slashes (`//`) issue in the server URL when the user provides an incorrect format.
- Ensured output directory label persists even after clicking "Fetch Buckets."

### Known Issues

- Windows build still requires manual intervention for dependencies.
- Minor inconsistencies in archive naming conventions on Linux.

## [0.0.1] - 2024-12-18

### Added

- Initial release of ArchImmich with basic export functionality.
- Support for MacOS, Linux, and Windows builds.
- UI components for login, progress tracking, and archive management.
