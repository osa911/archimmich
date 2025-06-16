#!/bin/sh

# Add platform-specific options
case "$(uname)" in
  "Darwin")
    PLATFORM_OPTS="--osx-bundle-identifier com.osa911.archimmich"
    PLATFORM_DEPS="--debug all"
    ;;
  "Linux")
    PLATFORM_OPTS=""
    PLATFORM_DEPS=""
    ;;
  *)  # Windows
    PLATFORM_OPTS="--version-file=src/resources/version.rc"
    PLATFORM_DEPS="--collect-all PyQt5 --collect-all requests --collect-binaries _internal"
    ;;
esac

# Use wine on Windows
if [ "$(uname)" != "Darwin" ] && [ "$(uname)" != "Linux" ]; then
  PYINSTALLER="wine python3 -m PyInstaller"
else
  # Try pyinstaller command first, fallback to python module
  if command -v pyinstaller >/dev/null 2>&1; then
    PYINSTALLER="pyinstaller"
  else
    PYINSTALLER="python3 -m PyInstaller"
  fi
fi

# Clean previous builds
rm -rf build dist

$PYINSTALLER \
  --onedir \
  --windowed \
  --optimize "2" \
  --icon="src/resources/favicon-180.png" \
  --add-data "src/resources/*:src/resources" \
  --add-data "version.txt:." \
  --paths="src" \
  --name "ArchImmich" \
  $PLATFORM_OPTS \
  $PLATFORM_DEPS \
  src/main.py;