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

# Set the output filename
TARBALL="release/ArchImmich_Linux_v${VERSION}.tar.gz"

# Remove existing tarball if it exists
if [ -f "$TARBALL" ]; then
    echo "Removing existing tarball..."
    rm "$TARBALL"
fi

# Create a tarball with the version included in the filename
echo "Creating Linux tarball..."
tar -czf "$TARBALL" -C dist ArchImmich

# Verify the tarball was created
if [ -f "$TARBALL" ]; then
    echo "Successfully created: $TARBALL"
else
    echo "Error: Failed to create tarball"
    exit 1
fi