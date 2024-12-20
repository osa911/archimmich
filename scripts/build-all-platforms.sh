# #!/bin/sh

# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# rm -rf dist build release;
# # build all platforms
# sh "$SCRIPT_DIR/build-macos.sh" && sh "$SCRIPT_DIR/build-linux.sh" && sh "$SCRIPT_DIR/build-windows.sh";


#!/bin/bash

set -e  # Exit on error

# Get the directory of the build-all.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rm -rf release;

# Ensure release folder exists
mkdir -p "$SCRIPT_DIR/../release"

# Get version from version.txt
VERSION=$(cat "$SCRIPT_DIR/../version.txt")

# 1. Build for macOS
echo "Starting macOS build..."
rm -rf dist build;
sh "$SCRIPT_DIR/build-macos.sh"
echo "macOS build completed!"

# 2. Build for Linux
echo "Starting Linux build..."
rm -rf dist build;
docker run --rm -v "$SCRIPT_DIR/../:/app" -w /app python:3.11-bullseye \
    /bin/bash -c "
    pip install pyinstaller;
    sh /app/scripts/build-linux.sh;"
echo "Linux build completed!"

# 3. Build for Windows
echo "Starting Windows build..."
rm -rf dist build;
sh "$SCRIPT_DIR/build-windows.sh"
echo "Windows build completed!"

echo "All builds completed successfully! Check the 'release' folder for artifacts."