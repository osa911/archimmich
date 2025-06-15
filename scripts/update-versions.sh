#!/bin/sh

# Check if version argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.0.4"
    exit 1
fi

VERSION=$1

# Update version.txt
echo "$VERSION" > version.txt

# Update src/__init__.py
# Using sed with different syntax for macOS and Linux
if [ "$(uname)" = "Darwin" ]; then
    # macOS version
    sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/__init__.py
else
    # Linux/Unix version
    sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/__init__.py
fi

echo "Version updated to $VERSION in:"
echo "- version.txt"
echo "- src/__init__.py"