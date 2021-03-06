#!/usr/bin/env python

"""subsample an alignment using beta distributions (with hard-coded parameters) to model sampling probabilities"""

if __name__ == '__main__':

    import argparse, copy, operator, os, random, re, sys 
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument("-a", "--alignment-file", required=True, type=open, help="The name of the alignment in relaxed phylip format, to be subsampled.")

    parser.add_argument("-p", "--partitions-file", required=True, type=open, help="The name of the partitions file, in raxml format, to be used.")

    parser.add_argument("-r", "--random-seed", type=int, help="A random seed to use.") 

    parser.add_argument("-l", "--label", help="A label to be used for output files.") 
    
    parser.add_argument("-o", "--order", help="A list of the partitions in decreasing order of rate, used to ensure that faster evolving ones are subsampled less.")

    args = parser.parse_args()

    if 'random_seed' in args:
        random.seed(args.random_seed)
    else:
        random.seed()

    output_label = args.output_label if 'output_label' in args else args.alignment_file.name.rsplit('.',1)[0]

    order = args.order.split(',') if 'order' in args else None

    # map the partitions to a dict
    part_start_map = {}
    parts = {}
    for line in args.partitions_file:
        toks = [t.strip() for t in re.split(r'[,=]+',line)]
        ptype = toks[0]
        name = toks[1]
        bounds = [b.strip() for b in toks[2].split("-")]
        start = int(bounds[0])
        end = int(bounds[1])
#        parts[start] = { 'name': name, 'type': ptype, 'start': start, 'end': end, 'taxa_sampled': 0, 'data': {}, }
        parts[name] = { 'name': name, 'type': ptype, 'start': start, 'end': end, 'taxa_sampled': 0, 'data': {}, }
        part_start_map[start] = name
    part_starts = sorted(part_start_map.keys())
    args.partitions_file.close()
    
    # read in the alignment, recording the taxon names in a separate dict
    taxa = {}
    ntax = 0
    ncols = 0
    on_first_line = True
    for line in args.alignment_file:
        if len(line.strip()) < 3:
            continue
        toks = [l.strip() for l in line.split()]
        if len(toks) > 1:
            if on_first_line == True:
                on_first_line = False
                ntax = toks[0]
                ncols = toks[1]
                print ntax, ncols
                if parts is None:
                    parts = {'all': { 'name': 'all', 'type': 'DNA', 'start': 1, 'end': int(ncols), 'taxa_sampled': 0, 'data': {}, }}
                    part_starts = {1: 'all'}
            else:
                taxname = toks[0]
                seq = toks[1]
                taxa[taxname] = {'parts_sampled': 0}
                for start in part_starts:
                    n = part_start_map[start]
                    end = parts[n]['end']
                    parts[n]['data'][taxname] = seq[start-1:end]
        else:
            raise IndexError("too many items on line '" + line + "' in alignment") 
    args.alignment_file.close()

    # assign sampling probs for loci from beta distribution a=3, b=5.
    # chance of drawing a sampling prob 0.1 < S < 0.71 is 95%
#    p = np.random.beta(3,5,len(parts))
#    for i, s in enumerate(parts.keys()):
#        parts[s]['p'] = p[i]

    # for 10% of loci (minimum 1), assign sampling probs from beta dist a=4, b=3.
    # chance of drawing a sampling prob 0.22 < S < 0.88 is 95%
#    lucky_parts = random.sample(parts.keys(), max(len(parts)/10,1))
#    p = np.random.beta(4,3,len(lucky_parts))
#    for i, s in enumerate(lucky_parts):
#        parts[s]['note'] = 'p increased from ' + str(parts[s]['p']) + ' to ' + str(p[i])
#        parts[s]['p'] = p[i]

    n_lucky_parts = max(len(parts)/10,1)
    probs = list(np.random.beta(4,3,n_lucky_parts))
    for p in np.random.beta(3,5,len(parts) - n_lucky_parts):
        probs.append(p)

    probs.sort(reverse=True)
    for i, n in enumerate(order if order is not None else parts):
        print i, n
        parts[n]['p'] = probs[i]

    # assign sampling probs for taxa from beta distribution a=3, b=5.
    # chance of drawing a sampling prob 0.1 < S < 0.71 is 95%
    p = np.random.beta(3,5,len(taxa))
    for i, t in enumerate(taxa.keys()):
        taxa[t]['p'] = p[i]

    # for 5% of taxa (minimum 1), assign sampling probs from beta dist a=8, b=1.
    # chance of drawing a sampling prob MORE than 0.68 is 95%
    lucky_taxa = random.sample(taxa.keys(), max(len(taxa)/20,1))
    p = np.random.beta(8,1,len(lucky_taxa))
    for i, t in enumerate(lucky_taxa):
        taxa[t]['note'] = 'p increased from ' + str(taxa[t]['p']) + ' to ' + str(p[i])
        taxa[t]['p'] = p[i]
    
    # precalculate proposal values for all cells in the sampling matrix
    p = np.random.uniform(0, 1, len(taxa) * len(parts))

    sample_bitmap = {}
    i = 0
    k = 0 # count of sampled sites
    for t in taxa:
        if t not in sample_bitmap:
            sample_bitmap[t] = {}

        for n in parts:
            if n not in sample_bitmap[t]:
                sample_bitmap[t][n] = {}

            if parts[n]['p'] * taxa[t]['p'] > p[i]:
                sample_bitmap[t][n] = True
                parts[n]['taxa_sampled'] += 1
                taxa[t]['parts_sampled'] += 1
                k += 1
            else:
                sample_bitmap[t][n] = False

            i += 1
        
        # open a random site, to be sure we have at least one sampled partition for all taxa
        r = parts.keys()[random.randrange(len(parts))]
        if sample_bitmap[t][r] != True:
            taxa[t]['parts_sampled'] += 1
        sample_bitmap[t][r] = True
    
    # create iterators over the dicts to return data in sorted order
    taxa_sorted = sorted(taxa.items(), cmp=lambda p, q: cmp(p[1]['parts_sampled'], q[1]['parts_sampled']), reverse=True)
    parts_sorted = sorted(parts.items(), cmp=lambda p, q: cmp(p[1]['taxa_sampled'], q[1]['taxa_sampled']), reverse=True)

    with open(output_label + '.sampling_matrix.txt', 'w') as sampling_matrix:
        for t in taxa_sorted:
            for p in parts_sorted:
                if sample_bitmap[t[0]][p[0]]:
                    sampling_matrix.write('1')
                else:
                    sampling_matrix.write('0')
            sampling_matrix.write('\n')

    with open(output_label + '.subsampled.phy', 'w') as subsampled_aln:
        subsampled_aln.write(ntax + ' ' + ncols + "\n")
        for t in taxa_sorted:
            subsampled_aln.write(t[0] + ' ')
            for p in parts_sorted:
                if sample_bitmap[t[0]][p[0]]:
                    subsampled_aln.write(parts[p[0]]['data'][t[0]])
                else:
                    subsampled_aln.write('-' * len(parts[p[0]]['data'][t[0]]))
            subsampled_aln.write("\n")

    print('files have been written to: ' + output_label + '.sampling_matrix.txt, ' + output_label + '.subsampled.phy\n' \
          'sampling proportion is ' + str(float(k) / (len(parts) * len(taxa))))
