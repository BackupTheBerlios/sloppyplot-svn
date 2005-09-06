#!/bin/sh
rm -rf API_Documentation
mkdir API_Documentation
epydoc -n sloppyplot -u http://sloppyplot.berlios.de -o API_Documentation src/Sloppy
