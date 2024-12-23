# Changelog

All notable changes to this project will be documented in this file.

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
