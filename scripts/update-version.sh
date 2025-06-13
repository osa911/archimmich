#!/bin/bash

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Please provide version number (e.g., 0.0.1)"
    exit 1
fi

VERSION=$1

# Update version.txt
echo $VERSION > version.txt

# Update constants.py
sed -i.bak "s/VERSION = \".*\"/VERSION = \"$VERSION\"/" src/constants.py
rm src/constants.py.bak

# Update Info.plist
sed -i.bak "s/<string>[0-9]\.[0-9]\.[0-9]<\/string>/<string>$VERSION<\/string>/" src/resources/Info.plist
rm src/resources/Info.plist.bak

# Update version.rc
# Convert version string to tuple format (e.g., 0.0.1 -> 0, 0, 1, 0)
VERSION_TUPLE=$(echo $VERSION | awk -F. '{print "(" $1 ", " $2 ", " $3 ", 0)"}')
sed -i.bak "s/filevers=([0-9], [0-9], [0-9], [0-9])/filevers=$VERSION_TUPLE/" src/resources/version.rc
sed -i.bak "s/prodvers=([0-9], [0-9], [0-9], [0-9])/prodvers=$VERSION_TUPLE/" src/resources/version.rc
sed -i.bak "s/u'FileVersion', u'[0-9]\.[0-9]\.[0-9]'/u'FileVersion', u'$VERSION'/" src/resources/version.rc
sed -i.bak "s/u'ProductVersion', u'[0-9]\.[0-9]\.[0-9]'/u'ProductVersion', u'$VERSION'/" src/resources/version.rc
rm src/resources/version.rc.bak

# Update desktop file
sed -i.bak "s/Version=.*/Version=$VERSION/" src/resources/archimmich.desktop
rm src/resources/archimmich.desktop.bak

echo "Version updated to $VERSION in all files"