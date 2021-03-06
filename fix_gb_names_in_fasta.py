#!/usr/bin/env python

"""Cleans the namestrings in fasta files downloaded from ncbi, saving only minimal name information with no special characters. Optionally will use an interactive prompt to allow the user to rename things with names in unrecognized formats"""

import re
import string
import sys

def clear_screen():
	"""Clear screen, return cursor to top left"""
	sys.stdout.write('\033[2J')
	sys.stdout.write('\033[H')
	sys.stdout.flush()

def bold(msg):
	return u'\033[1m%s\033[0m' % msg

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "usage: fixgbnames_fasta <fasta_file> [<suppress_rename_prompt: Y/N>]"
		sys.exit(0)

	infname = sys.argv[1]
	suppress_rename_prompt = False
	if len(sys.argv) > 2:
		if sys.argv[2].upper() == "Y":
			suppress_rename_prompt = True

	addlchars = 50
	legal_punc_list = list(string.punctuation)
	legal_punc_list.remove('-')
	illegal_chars = ''.join(legal_punc_list)

	subsp_tax_ids = dict([ \
	   ("ssp.", "subsp."), \
	   ("subsp.", "subsp."), \
	   ("subspecies", "subsp."), \
	   ("v.", "var."), \
	   ("var.", "var."), \
	   ("variety", "var."), \
	   ("f.", "form"), \
	   ("form", "form"), \
	   ("forma", "form")])

	try:
	   infile = open(infname,"rb")
	except IOError:
	   exit("the specified infile could not be opened.")

	try:
		outfile = open(infname + ".namesfixed","wb")
	except IOError:
		exit("could not open the output file")

	results = list()
	curseq = ""
	for line in infile:

		tokens = string.split(line)

		if len(tokens) < 2:
			# this is not a name line (i.e. it is a nucleotide sequence), save it
			curseq += line
		else:
			# this is a new name line
			try:
				# add any saved sequence data to the results under last saved taxon name, reset seq and name
				item = {"name": taxon["name"], "seq": curseq, "flagged": taxon["flagged"]}			
	#			print item["name"]

				results.append(item)
				curseq = ""

			except NameError:
				# if this is the first name line, (i.e. no saved name or sequence) then skip it
				pass

			# start processing new name
			taxon = dict()
			taxon["flagged"] = False

			first_tok = True
			save_next = False
			genus = False
			species = False
			subsp_tax = False

			for token in tokens:

				if not save_next:
					if first_tok:
						first_tok = False
						save_next = True
						genus = True
					else:
						if token in subsp_tax_ids:
							subsp_tax = True
							subsp_tax_type = subsp_tax_ids[token]
							save_next = True
				else:
					if genus:
						taxon["genus"] = token
						genus = False
						species = True

						match = re.search("[" + illegal_chars + "]",token)
						if match != None:
							strpos = string.find(line, token)
							taxon["species"] = string.strip(line[strpos + len(token):strpos + addlchars])

							if len(line) > strpos + len(token) + addlchars:
								taxon["species"] += "..."

							taxon["flagged"] = True
							break

					elif species:
						if token == "sp.":
							strpos = string.find(line, token)
							taxon["species"] = line[strpos:strpos + addlchars]

							if len(line) > strpos + addlchars:
								taxon["species"] += "..."

							taxon["flagged"] = True
							break

						else:

							taxon["species"] = token

							match = re.search("[" + illegal_chars + "]",token)
							if match != None:
								strpos = string.find(line, token)
								taxon["subsp"] = string.strip(line[strpos + len(token):strpos + addlchars])

								if len(line) > strpos + len(token) + addlchars:
									taxon["species"] += "..."

								taxon["flagged"] = True
								break

						species = False

					elif subsp_tax:
						strpos = string.find(line, token) + len(token)
						taxon["subsp"] = subsp_tax_type + " " + line[strpos:strpos + addlchars]

						if len(line) > strpos + addlchars:
							taxon["subsp"] += "..."

						taxon["flagged"] = True
						break

		taxon["name"] = taxon["genus"] + " " + taxon["species"]

		try:
			taxon["name"] += " " + taxon["subsp"]
		except KeyError:
			pass

	# save the last item from the previous loop
	item = {"name": taxon["name"], "seq": curseq, "flagged": taxon["flagged"]}
	results.append(item)		

	saved = dict()
	flagged = list()
#	clear_screen()
	for item in results:
		if item["flagged"]:
			flagged.append(item)
		else:
			clean_name = re.sub("[" + illegal_chars + "\s]+", "_", item["name"])
			saved[clean_name] = item["seq"]
			print "Accepted '" + clean_name + "' " + str(len(item["seq"])) + " bp"

	print "\n " + str(len(flagged)) + " items were flagged.\n" 

	for item in flagged:
		print item["name"]

	for item in flagged:
		if suppress_rename_prompt:
			new_name = re.sub("[" + illegal_chars + "\s]+", "_", item["name"][0:50])
			saved[new_name] = item["seq"]
			continue

		print "\n%s" % bold(item["name"])
		print "\nThe validity of this taxon is uncertain. Enter a number to:\n" \

		choice = ""
		while choice not in [1,2,3,99]:
			print "1. Remove it\n2. Rename it\n3. Do nothing (keep it, using the current name)\n99. exit script, saving nothing"
			response = raw_input()
			resp_toks = string.split(str(response))
			try:
				choice = int(resp_toks[0])
			except (ValueError, IndexError):
				pass

	#	print response

		if choice == 99:
			exit("No output saved")

		elif choice == 1:
			print "Removed."

		elif choice == 2:
			if len(resp_toks) > 2:
				addl_msg = ""
				new_name_toks = resp_toks[1:len(resp_toks)]
			else:
				new_name_raw = raw_input("\nPlease enter a new name for this taxon in one of the following formats:\n" \
					"[genus] [specific epithet]\n" \
					"[genus] [specific epithet] subsp. / var. / form [subsp epithet]\n" \
					"[genus] sp. [species identifier]\n")
				new_name_toks = string.split(new_name_raw)
				addl_msg = 	"\n\nNext time you can skip this prompt by entering a space followed\n" \
					"by the new name after the response \"2\" to the previous prompt."

			valid_name = False
			while not valid_name:

				new_name = ""

				if len(new_name_toks) == 1 and new_name_toks[0] == 'q':
					exit("No output saved")

				elif len(new_name_toks) == 2:
					print "DEBUG"
					for token in new_name_toks:
						match = re.search("[" + illegal_chars + "]",token)
						if match == None:
							new_name += token + " "
						else:
							break

					new_name.strip()
					valid_name = True;

				elif len(new_name_toks) == 4:
					subsp_tax_id = new_name_toks[2].strip(".")
					if subsp_tax_id == "subsp." or subsp_tax_id == "var." or subsp_tax_id == "form":
						for token in new_name_toks[0:2] + new_name_toks[3]:
							match = re.search("[" + illegal_chars + "]",token)
							if match != None:
								break

					new_name = ' '.join(new_name_toks[0:2] + [new_name_toks[2].strip(".")] + [new_name_toks[3]])
					valid_name = True

				elif len(new_name_toks) > 2 and new_name_toks[1].strip(".") == "sp":
					for token in new_name_toks[0:1] + new_name_toks[2:len(new_name_toks)]:
						match = re.search("[" + illegal_chars + "]",token)
						if match != None:
							break

					new_name = ' '.join(new_name_toks[0:1] + ['sp'] + new_name_toks[2:len(new_name_toks)])
					valid_name = True

				else:
					resp = raw_input("That name was not in a valid format. Try again, or enter 'q' to exit:\n")
					new_name_toks = resp.split()


			new_name = re.sub("[" + illegal_chars + "\s]+", "_", new_name.strip(" ."))
			saved[new_name] = item["seq"]
			print "\nSaved under %s. %s" % (bold(new_name), addl_msg)


		elif choice == 3:
			new_name = item["name"].strip(". ")
			saved[new_name] = item["seq"]
			print "\nSaved under " + new_name


	for name, seq in saved.iteritems():
		outfile.write(">" + name + "\n")
		outfile.write(seq)

	outfile.flush()
	exit("Success! Cleaned names written to " + outfile.name)

