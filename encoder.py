# Usage: python encoder.py myfile.tex
# encodes a lossless compression of a LaTeX file
import sys
import os

file_name = sys.argv[1]

name, extension = os.path.splitext(file_name)
print("File name: ", name)
print("File extension: ", extension)

if extension != ".tex":
    print("Not a LaTeX file!")
    exit()

file = open(file_name, 'r')
print("File: ", file)

if file.mode == 'r':
    file_contents = file.read()
    print("File contents: ", file_contents)
