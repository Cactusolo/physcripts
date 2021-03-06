#!/usr/bin/env python

import sys
import os

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "usage: phylip2fasta <phylipfile> <outfile>"

    try:
        inpath = sys.argv[1]
        infile = open(inpath,"rU")
    except OSError:
        exit("There was a problem opening the specified directory. Are you sure it exists? Quitting.")

    outfile = open(sys.argv[2],"w")

    firstline = True
    for bits in [line.strip().split() for line in infile.readlines()]:

        if len(bits) > 0:
            if firstline:
                firstline = False
                continue

            name, seq = bits
            outfile.write(">" + name + "\n")
            outfile.write(seq + "\n")

    infile.close()
    outfile.close()
