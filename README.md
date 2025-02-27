# PNG Image Processing Assignment

## Overview
This project is a Python implementation for reading, processing, and saving PNG image files. The assignment involves creating a class named `PNG` that can handle PNG files, extract image data, and save specific color channels (red, green, or blue) as separate PNG files. The implementation adheres to a subset of the PNG specification, focusing on the `IHDR`, `IDAT`, and `IEND` chunks.

## Assignment Details
The goal of this assignment is to develop a Python class that can:
1. Load a PNG file and store its data.
2. Validate the PNG file by checking its signature.
3. Read the image header (`IHDR`) to extract metadata such as width, height, bit depth, and color type.
4. Process the image data chunks (`IDAT`) to extract pixel data.
5. Save specific color channels (red, green, or blue) as new PNG files.
