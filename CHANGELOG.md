# Changelog

All notable changes to this project will be documented in this file.

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
