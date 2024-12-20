#!/bin/bash

# Read the version from version.txt
VERSION=$(cat version.txt)

# Create a tarball with the version included in the filename
echo "Packaging Linux build..."
tar -cvzf "release/ArchImmich_Linux_v${VERSION}.tar.gz" dist/ArchImmich

# Print success message
echo "Archive created: ArchImmich_Linux_v${VERSION}.tar.gz"