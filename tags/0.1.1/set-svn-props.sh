#!/usr/bin/sh

echo "Setting SVN properties..."
for f in `find . -iname "*.py"`; do
  echo "[$f]"
  svn ps svn:keywords "HeadURL Rev Id" $f
done
