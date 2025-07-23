# **ArchImmich**
![Downloads](https://img.shields.io/github/downloads/osa911/archimmich/total?label=Downloads)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/osa911/archimmich)](https://github.com/osa911/archimmich/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/osa911/archimmich)](https://github.com/osa911/archimmich/stargazers)

**ArchImmich** is a modern export and archive tool designed for users of the Immich platform. This application simplifies the process of fetching media buckets and exporting them into archives, all while offering a sleek and user-friendly interface.

<div align="center">
    <img src="https://github.com/user-attachments/assets/439721f1-ee8c-49fa-ad75-b7bcad8f5ad0" alt="ArchImmich UI">
</div>

## **Download**

You can download the latest version of ArchImmich from the official GitHub releases page:

1. Go to the [Releases page](https://github.com/osa911/archimmich/releases)
2. Download the appropriate version for your operating system:
   - **Linux**: `ArchImmich_Linux_vX.X.X.tar.gz`
   - **MacOS**: `ArchImmich_MacOS_vX.X.X.dmg`
   - **Windows**: `ArchImmich_Windows_vX.X.X.zip`

## **Installation**

1. Extract the downloaded archive
2. Run the application:
   - **Linux**: Unzip the archive and run `./ArchImmich`
   - **MacOS**: Double-click on `ArchImmich_MacOS_vX.X.X.dmg` and move `ArchImmich.app` to your Applications folder
   - **Windows**: Unzip the archive and double-click `ArchImmich.exe`

## **Features**

- **Fetch Media Buckets**:
  Retrieve buckets of media files grouped by day or month.

- **Customizable Export Options**:

  - Archive size configuration.
  - Group files into single or multiple archives.

- **Real-Time Progress**:

  - General and per-download progress bars.
  - Logs for detailed insights.

- **Integrity Validation**:

  - Check existing archives to avoid redundant downloads.

- **User-Friendly Interface**:
  - Modern UI with intuitive options for configuration and archive management.

## **Installation from Source**

### **1. Clone the Repository**

```bash
git clone https://github.com/osa911/archimmich.git
cd archimmich
```

### **2. Install Dependencies**

Make sure you have **Python 3.7 or higher** installed. Then, set up your virtual environment and install the required packages:

1. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment**:

   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     venv\\Scripts\\activate
     ```

3. **Install the required packages**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the .env file**:
   - Create a `.env` file in the root directory from the provided `.env.example` file.

### **3. Run the Application**

Start the application with:

```bash
python3 src/main.py
```

---

## **Running Tests**

ArchImmich includes a comprehensive test suite to ensure code quality and functionality. To run the tests:

1. **Setup your test environment**:

   ```bash
   # Make sure you're in the project root directory
   # Activate your virtual environment if not already active
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install test dependencies
   pip install pytest pytest-mock pytest-qt
   ```

2. **Run all tests**:

   ```bash
   # From the project root directory
   pytest
   ```

3. **Run specific test files**:

   ```bash
   pytest tests/test_helpers.py
   ```

4. **Run tests with verbose output**:

   ```bash
   pytest -v
   ```

5. **Run tests with coverage report**:
   ```bash
   pip install pytest-cov
   pytest --cov=src
   ```

When contributing new features, please ensure that you add appropriate tests and that all existing tests pass.

---

## Building into standalone applications

To package the application into standalone executables for all platforms:

### Quick Start

```bash
# Install PyInstaller (if building locally)
pip install pyinstaller

# Build for all platforms
./scripts/build-all-platforms.sh
```

### Platform-Specific Builds

```bash
./scripts/build-macos.sh    # macOS .dmg
./scripts/build-linux.sh    # Linux .tar.gz (uses Docker)
./scripts/build-windows.sh  # Windows .zip (uses Wine)
```

### Build Output

The built applications will be available in the `release/` directory:

- `ArchImmich_MacOS_v{version}.dmg` - macOS disk image
- `ArchImmich_Linux_v{version}.tar.gz` - Linux package
- `ArchImmich_Windows_v{version}.zip` - Windows package with `.exe`

### Cross-Platform Building Setup

#### Windows Builds on macOS/Linux (using Wine)

To build Windows `.exe` files on macOS or Linux, you need Wine with Windows Python:

1. **Install Wine**:

   ```bash
   # macOS (using Homebrew)
   brew install wine-stable

   # Ubuntu/Debian
   sudo apt install wine
   ```

2. **Install Windows Python in Wine** (one-time setup):

   ```bash
   # Download and install Python for Windows
   curl -L -o /tmp/python-3.11.6-amd64.exe https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe
   wine /tmp/python-3.11.6-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
   rm /tmp/python-3.11.6-amd64.exe
   ```

3. **Install PyInstaller and dependencies in Wine**:

   ```bash
   wine python -m pip install pyinstaller PyQt5 requests Pillow
   ```

4. **Verify setup**:

   ```bash
   wine python --version        # Should show Python 3.11.6
   wine pyinstaller --version   # Should show PyInstaller version
   ```

5. **Build Windows executable**:
   ```bash
   ./scripts/build-windows.sh   # Now creates proper .exe files
   ```

#### Linux Builds (using Docker)

Linux builds automatically use Docker with Python 3.11 to ensure compatibility.

#### macOS Builds

macOS builds run natively and create `.dmg` packages using `create-dmg`.

### Build Requirements

- **macOS**: `create-dmg` (install via `brew install create-dmg`)
- **Linux**: Docker
- **Windows**: Wine with Windows Python and PyInstaller (see setup above)

### Quick Wine Setup (for Windows builds)

If you need to set up Wine for Windows builds, run these commands:

```bash
# Install Wine (macOS)
brew install wine-stable

# One-time Wine setup for Windows builds
curl -L -o /tmp/python-3.11.6-amd64.exe https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe
wine /tmp/python-3.11.6-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
wine python -m pip install pyinstaller PyQt5 requests Pillow
rm /tmp/python-3.11.6-amd64.exe

# Verify setup
wine python --version && wine pyinstaller --version
```

### Troubleshooting

**Wine Issues**:

- If Wine setup fails, try: `winecfg` to initialize Wine configuration
- Ensure Wine prefix is clean: `rm -rf ~/.wine && winecfg`

**Build Failures**:

- Check that all dependencies are installed in the target environment
- For Wine builds, verify: `wine python -c "import PyQt5; print('PyQt5 OK')"`

---

## **Usage**

1. **Login**:

   - Enter your **API key** and **server URL**.
   - Click **Login** to authenticate with the Immich server.

2. **Configure Export**:

   - Choose archive size and the output directory.

3. **Fetch Buckets**:

   - Click **Fetch Buckets** to list available media buckets.
   - Select the desired buckets for export.

4. **Export**:

   - Start the export process and monitor progress in the logs and progress bars.

5. **Access Archives**:
   - Use the **Open Folder** button to access exported archives.

## **Logs**

ArchImmich automatically logs all operations to help with troubleshooting:

- **Log Location**:

  - Logs are stored in the user data directory for persistence across app updates
  - Each session creates a new log file

  **Examples:**

  - **Windows**: `%APPDATA%\ArchImmich\logs\archimmich_20240612_123456.log`
  - **macOS**: `~/Library/Application Support/ArchImmich/logs/archimmich_20240612_123456.log`
  - **Linux**: `~/.config/ArchImmich/logs/archimmich_20240612_123456.log`
  - **From Source**: `~/.config/ArchImmich/logs/archimmich_20240612_123456.log`

- **Log Format**:

  - Log files are named with timestamps: `archimmich_YYYYMMDD_HHMMSS.log`
  - Each log entry includes timestamp, level, and message

- **Log Contents**:
  - Application startup/shutdown
  - Login attempts
  - API operations
  - Download progress
  - Errors and warnings

## **Configuration**

ArchImmich stores your configuration in a JSON file:

- **Config Location**:

  - The config file is stored as `config.json` in the user data directory for persistence across app updates

  **Examples:**

  - **Windows**: `%APPDATA%\ArchImmich\config.json`
  - **macOS**: `~/Library/Application Support/ArchImmich/config.json`
  - **Linux**: `~/.config/ArchImmich/config.json`
  - **From Source**: `~/.config/ArchImmich/config.json`

- **Config Contents**:
  - Server URL
  - API key
  - User preferences

If you encounter any issues with the application, please include the relevant log files when reporting problems.

---


## **Screenshots**

| light theme                                                                               | dark theme                                                                                |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| ![image](https://github.com/user-attachments/assets/f45d2f57-ff7c-48f6-ae00-dcbdc5b4b1e9) | ![image](https://github.com/user-attachments/assets/439721f1-ee8c-49fa-ad75-b7bcad8f5ad0) |

---

## **Contributing**

1. Fork the repository.
2. Create a new feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

## **Version Management**

When releasing a new version:

1. **Update Version**:

   ```bash
   # Update version across all files
   sh scripts/update-version.sh X.X.X  # Replace X.X.X with version number
   ```

   This script updates version numbers in:

   - `version.txt`
   - `src/constants.py`
   - `src/__init__.py`
   - `src/resources/Info.plist`
   - `src/resources/version.rc`
   - `src/resources/archimmich.desktop`

2. **Build All Platforms**:

   ```bash
   sh scripts/build-all-platforms.sh
   ```

3. **Create Release**:
   - Tag the version in git
   - Create a GitHub release
   - Upload the built artifacts

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

---

## **Contact**

For feedback, issues, or questions:

- **GitHub Issues**: [https://github.com/osa911/archimmich/issues](https://github.com/osa911/archimmich/issues)

## Author

[Osa911](https://github.com/osa911)
