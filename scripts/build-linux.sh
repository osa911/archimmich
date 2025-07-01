#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run pyinstaller.sh and create-dmg.sh with paths relative to the script
echo "Building for Linux..."
sh "$SCRIPT_DIR/pyinstaller.sh" && sh "$SCRIPT_DIR/create-tar.gz.sh";