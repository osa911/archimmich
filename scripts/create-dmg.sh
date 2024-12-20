# Ensure the release folder exists
mkdir -p release;

# get the version
VERSION=$(cat version.txt)

# Create the DMG file
echo "Creating macOS DMG..."
create-dmg \
  --volname "ArchImmich" \
  --window-size 550 350 \
  --icon "ArchImmich.app" 150 100 \
  --hide-extension "ArchImmich" \
  --app-drop-link 400 100 \
  "release/ArchImmich_MacOS_v$VERSION.dmg" "dist/ArchImmich.app";