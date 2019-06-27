import ctypes

class Pair(ctypes.Structure):
	_fields_ = [("first", ctypes.c_float), ("second", ctypes.c_float)]
	def __init__(self,first,second=None):
		self.first=first
		if second == None:
			self.second=first
		else:
			self.second=second


class MlcInformation(ctypes.Structure):
	_fields_ = [("numberLeaves", ctypes.c_int), ("leftLeaves", ctypes.POINTER(Pair)), ("rightLeaves", ctypes.POINTER(Pair))]
	def __init__(self,numberLeaves):
		self.leftLeaves_data = (Pair * numberLeaves)()
		self.rightLeaves_data = (Pair * numberLeaves)()
		self.leftLeaves = ctypes.cast(self.leftLeaves_data,ctypes.POINTER(Pair))
		self.rightLeaves = ctypes.cast(self.rightLeaves_data,ctypes.POINTER(Pair))
		self.numberLeaves = numberLeaves

class noname():
	def __init__(self):
		self.sim = (ctypes.c_float * 10)()
		self.com = (Pair * 10)()
		self.mlc = (MlcInformation * 10)(MlcInformation(80))
		self.mlc_enkel = MlcInformation(80)

nn=noname()

nn.sim[3]=3e4
nn.com[2]=Pair(0.653)
print(nn.sim[3],nn.com[2].second) #tot zover alles goed

nn.mlc[7]=MlcInformation(80)
nn.mlc[7].leftLeaves_data[50] = Pair(3.1415) #doesnt work
# nn.mlc[7].leftLeaves[50] = Pair(3.1415) #does work, but allocates new Pair not in the leftLeaves_data array, correct?
print(nn.mlc[0].leftLeaves[50].first)

apart=MlcInformation(80)
nn.mlc_enkel.leftLeaves_data[50] = Pair(2.72) #nu wordt leftLeaves_data wel gevonden
print(nn.mlc_enkel.leftLeaves_data[50].first)
