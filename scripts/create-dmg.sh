#!/bin/sh

# Exit on error
set -e

# Ensure the release folder exists
mkdir -p release

# Get the version
if [ ! -f version.txt ]; then
    echo "Error: version.txt not found"
    exit 1
fi

VERSION=$(cat version.txt)

# Check if the app exists
if [ ! -d "dist/ArchImmich.app" ]; then
    echo "Error: dist/ArchImmich.app not found. Please build the app first."
    exit 1
fi

# Remove existing DMG if it exists
DMG_PATH="release/ArchImmich_MacOS_v$VERSION.dmg"
if [ -f "$DMG_PATH" ]; then
    echo "Removing existing DMG..."
    rm "$DMG_PATH"
fi

# Create the DMG file
echo "Creating macOS DMG..."
create-dmg \
    --volname "ArchImmich" \
    --window-size 550 350 \
    --icon "ArchImmich.app" 150 100 \
    --hide-extension "ArchImmich.app" \
    --app-drop-link 400 100 \
    "$DMG_PATH" "dist/ArchImmich.app"

echo "DMG created successfully at $DMG_PATH"