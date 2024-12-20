#!/bin/bash

# Get the directory of the build.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove existing build directories
rm -rf dist build;

# Run pyinstaller.sh and create-dmg.sh with paths relative to the script
echo "Building for macOS..."
sh "$SCRIPT_DIR/pyinstaller.sh" && sh "$SCRIPT_DIR/create-dmg.sh";