#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running build-windows.sh script..."
VERSION=$(cat version.txt)

# Run pyinstaller.sh and create-dmg.sh with paths relative to the script
echo "Building for Windows..."
wine python -m pip install pyinstaller;
wine pyinstaller \
  --onedir \
  --windowed \
  --optimize "2" \
  --icon="src/resources/favicon-180.png" \
  --add-data "src/resources/*:src/resources" \
  --distpath "dist" \
  --paths="src" \
  --name "ArchImmich" \
  src/main.py;

mkdir -p release
mv dist/ArchImmich/ArchImmich.exe release/ArchImmich_Windows_v${VERSION}.exe
echo "Windows build completed! Find your executable in release/windows/"