def getrtplanfile(filename):
	'''
	Look for rtplan file in a macfile. Recurses through included mac files.
	'''
	sourcefile = open(filename,'r')

	rtfile = ""

	for index, line in enumerate(sourcefile):
		newline = line.strip()
		if len(newline)==0:
			continue

		newline=newline.split()

		if "/setPlan" in newline[0]:
			#we are reading the plan
			rtfile = newline[-1]

		if "/control/execute" in newline[0]:
			rtfile = getrtplanfile(newline[-1])

	sourcefile.close()

	return rtfile
