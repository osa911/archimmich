#!/bin/bash

# Get the directory of the build.sh script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove existing build directories
rm -rf dist build;

# Get version for package name
VERSION=$(cat version.txt)

# Run pyinstaller.sh
echo "Building for Windows..."
sh "$SCRIPT_DIR/pyinstaller.sh"

# Create zip package
mkdir -p release
cd dist/ArchImmich
zip -r ../../release/ArchImmich_Windows_v${VERSION}.zip ./*
cd ../..

echo "Windows build completed successfully!";