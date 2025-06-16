#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run pyinstaller.sh and create-dmg.sh with paths relative to the script
echo "Building for Linux..."
sh "/app/scripts/pyinstaller.sh" && sh "/app/scripts/create-tar.gz.sh";