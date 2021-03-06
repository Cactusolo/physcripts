#!/usr/bin/env python
'''Reads a newick tree with phlawd-style tip names -- <ncbi_id>_<genus>_<spepithet> -- and creates a line-delimited list of the generic names in the tree and their constituent species that is written to outfile. Names are just extracted and parsed with regex search, does not use the tree structure at all.'''

if __name__ == '__main__':

    import sys
    import os
    import re

    if len(sys.argv) < 3:
        print "usage: makegenustiplist.py <treefile> <outfile>"
        sys.exit(0)

    treefile = open(sys.argv[1],"r")
    taxnames = re.findall(r"[0-9]+_[-_A-Za-z0-9]+",treefile.readline())

    genus_lists = dict()
    for species_name in taxnames:
        genus_name = species_name.split("_")[1]
    
        if genus_name not in genus_lists.keys():
            genus_lists[genus_name] = list()

        genus_lists[genus_name].append(species_name)

    outfile = open(sys.argv[2],"w")
    for genus_name, species_list in genus_lists.iteritems():
        outfile.write(genus_name + "\n")

        for species_name in species_list:
            outfile.write("\t" + species_name + "\n")
