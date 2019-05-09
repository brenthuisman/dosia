import pydicom,sys

fname = sys.argv[-1]

data = pydicom.dcmread(fname,force=True)

# print(dir(data))


try:
	print (data.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID) # if fname is a dose, this value corresponds to the plan's SOPInstanceUID
except:
	print (data.SOPInstanceUID)

#print(dir(data.BeamSequence[0].ControlPointSequence[0]))

# for key, val in data.items():
# 	if str(key).startswith("_"):
# 		continue
# 	print(key, val)

# weights_beam_0 = []

# for cp in data.BeamSequence[0].ControlPointSequence:
# 	weights_beam_0.append( cp.CumulativeMetersetWeight )

# for i in range(len(weights_beam_0)):
# 	print(i, '\t', weights_beam_0[i], '\t', end="")
# 	try:
# 		weights_beam_0[i] = weights_beam_0[i+1] - weights_beam_0[i]
# 		print(weights_beam_0[i])
# 	except:
# 		pass


# was dis?:
#for beam in data.BeamSequence:
	#i = 0
	#for cp in beam.ControlPointSequence:
		##print(i,cp.CumulativeMetersetWeight)
		#weights_beam_0.append( cp.CumulativeMetersetWeight )
		#i+=1