#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

# Get script directory in a POSIX-compliant way
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Run pyinstaller.sh and create-tar.gz.sh with paths relative to the script
echo "Building for Linux..."
sh "$SCRIPT_DIR/pyinstaller.sh" && sh "$SCRIPT_DIR/create-tar.gz.sh"