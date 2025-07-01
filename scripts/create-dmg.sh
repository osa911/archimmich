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

# Function to create DMG with retries
create_dmg_with_retry() {
    max_attempts=3
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt of $max_attempts: Creating macOS DMG..."

        # Add a delay before creating DMG
        sleep 5

        if create-dmg \
            --volname "ArchImmich" \
            --window-size 550 350 \
            --icon "ArchImmich.app" 150 100 \
            --hide-extension "ArchImmich.app" \
            --app-drop-link 400 100 \
            "$DMG_PATH" "dist/ArchImmich.app"; then
            echo "DMG created successfully at $DMG_PATH"
            return 0
        fi

        echo "DMG creation failed on attempt $attempt"
        attempt=$((attempt + 1))

        # Clean up any failed attempts
        if [ -f "$DMG_PATH" ]; then
            rm "$DMG_PATH"
        fi

        # Wait before retrying
        if [ $attempt -le $max_attempts ]; then
            sleep 10
        fi
    done

    echo "Failed to create DMG after $max_attempts attempts"
    return 1
}

# Create the DMG file with retry logic
create_dmg_with_retry