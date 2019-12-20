import ctypes,os,medimage as image,dicom
from .accelerator import Accelerator
from .ct import CT
from .engine import Engine
from .rtplan import Rtplan
from .settings import Settings

class Dosia():
	''' This object will, given a plan, plandose and ct, handle a dose calculation for you, including running a few checks.'''

	def __init__(self,sett,ct,plan,plandose):
		assert(isinstance(sett,Settings))
		assert(isinstance(ct,image.image))
		assert(isinstance(plandose,image.image))
		assert(isinstance(plan,Rtplan))

		gpumcd_factor = False
		try:
			tpsdosespecpt = plandose.get_value(plan.BeamDoseSpecificationPoint)
			assert(plan.BeamDose*0.9 < tpsdosespecpt < plan.BeamDose*1.1)
		except:
			gpumcd_factor = True
			print("TPS dose it outside of expected planned dose per fraction in beamdosespecificationpoint. Your TPS probably exported the PLAN dose instead of FRACTION dose, GPUMCD dose will be multiplied with the number of fractions.")
		ctcpy = ct
		ctcpy.crop_as(plandose)
		ct_obj = CT(sett,ctcpy)
		ct_obj.dosemap.zero_out() #needed?

		self.gpumcd_dose = []
		if sett.dose['sum_beams'] == True:
			self.gpumcd_dose.append(ct_obj.dosemap.copy())

		for beam in plan.beams:
			if sett.dose['sum_beams'] == False:
				self.gpumcd_dose.append(ct_obj.dosemap.copy())
			#last index is now always current dosemap.

			eng=Engine(sett,ct_obj,plan.accelerator)
			eng.execute_segments(beam)
			if eng.lasterror()[0] != 0:
				print (eng.lasterror())
			eng.get_dose(self.gpumcd_dose[-1])

		for d in self.gpumcd_dose:
			if gpumcd_factor:
					d.mul(plan.NumberOfFractionsPlanned)
			else:
				# From what I've seen, dosemaps are exported per plan REGARDLESS of value of DoseSummationType. we try anyway.
				if plandose.DoseSummationType == 'PLAN':
					print("Dose was computed for whole PLAN, multiplying GPUMCD dose with number of fractions.")
					d.mul(plan.NumberOfFractionsPlanned)
				else:
					assert plandose.DoseSummationType == 'FRACTION'

		# self.gpumcd_dose = ct_obj.dosemap