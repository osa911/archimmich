#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running build-windows.sh script..."
VERSION=$(cat version.txt)

wine pyinstaller \
  --onedir \
  --windowed \
  --optimize "2" \
  --icon="src/resources/favicon-180.png" \
  --add-data "src/resources/*:src/resources" \
  --collect-binaries "_internal" \
  --distpath "dist" \
  --paths="src" \
  --name "ArchImmich" \
  --collect-all "PyQt5" \
  --collect-all "requests" \
  src/main.py;
mkdir -p release;
cd dist/ArchImmich;
zip -r ../../release/ArchImmich_Windows_v${VERSION}.zip ./*;
cd ../..;
echo "Windows build completed successfully!";