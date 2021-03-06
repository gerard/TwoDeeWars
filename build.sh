#!/bin/bash

# Set these according to your environment
ANDROIDAPI=14
ANDROIDNDKVER=r7
ANDROIDNDK=$HOME/android-ndk-$ANDROIDNDKVER
ANDROIDSDK=$HOME/android-sdk-linux
PATH=$ANDROIDNDK:$ANDROIDSDK/tools:$ANDROIDSDK/platform-tools:$PATH
PYTHONFORANDROID_DIST=$HOME/kivy/python-for-android/dist/default

BUILDTYPE=debug


while getopts ":o:i" OPT
do
    case $OPT in
    o)
        if [ "$OPTARG" = debug -o "$OPTARG" = release ]
        then
            BUILDTYPE=$opt
        else
            echo "E: Unknown build type: $OPTARG"
            exit 1
        fi
        ;;
    i)
        echo "I: APK will be installed after compilation"
        INSTALL=y
        ;;
    *)
        echo "E: Unknown option: -$opt"
        exit 1
    esac
done

echo "I: Making a $BUILDTYPE build"

cd `dirname $0`
PACKAGEDIR=$(readlink -f .)
PACKAGENAME=$(basename $PACKAGEDIR)

# Unfortunately the format of the version for apk is quite limited so we cannot
# include the full git describe as it is.
VERSION=`git describe | sed 's/^v//' | sed 's/-g.*//' | tr '-' '.'`
[ `git status --porcelain | wc -l` -ne "0" ] && VERSION=$VERSION.9

# This is needed so that build.py doesn't include all the files in the git
# repo.  It also helps to have build specific files included.
rm -rf build
mkdir build
cp -a main.py sounds build
mkdir build/.kivy
cp -a config/$BUILDTYPE/config.ini build/.kivy

cd $PYTHONFORANDROID_DIST
./build.py --dir $PACKAGEDIR/build \
           --name $PACKAGENAME \
           --package net.geeksynapse.geox.$PACKAGENAME \
           --version $VERSION $BUILDTYPE
cd -
rm -rf build

if [ "$INSTALL" = "y" ]
then
    set -x
    adb uninstall net.geeksynapse.geox.$PACKAGENAME
    adb install $PYTHONFORANDROID_DIST/bin/$PACKAGENAME-$VERSION-debug.apk
    set +x
fi
