#!/bin/bash

# Exit on error
set -e

# Ensure release directory exists
mkdir -p release

# Check if version.txt exists
if [ ! -f "version.txt" ]; then
    echo "Error: version.txt not found"
    exit 1
fi

# Read the version from version.txt
VERSION=$(cat version.txt)

# Check if build directory exists
if [ ! -d "dist/ArchImmich" ]; then
    echo "Error: dist/ArchImmich directory not found. Please build the app first."
    exit 1
fi

# Get architecture from environment or detect it
if [ -n "$TARGET_ARCH" ]; then
    ARCH="$TARGET_ARCH"
else
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        ARCH="arm64"
    else
        ARCH="x64"
    fi
fi

# Set the output filename with architecture
TARBALL="release/ArchImmich_Linux_${ARCH}_v${VERSION}.tar.gz"

# Remove existing tarball if it exists
if [ -f "$TARBALL" ]; then
    echo "Removing existing tarball..."
    rm "$TARBALL"
fi

# Create a tarball with the version included in the filename
echo "Creating Linux ${ARCH} tarball..."
tar -czf "$TARBALL" -C dist ArchImmich

# Verify the tarball was created
if [ -f "$TARBALL" ]; then
    echo "Successfully created: $TARBALL"
else
    echo "Error: Failed to create tarball"
    exit 1
fi