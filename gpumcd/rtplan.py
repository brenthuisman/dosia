from .settings import Settings
from .accelerator import Accelerator
from .ctypes_helpers import make_c_array
from .gpumcdwrapper import Segment, Pair, MlcInformation, ModifierOrientation, Float3
import dicom

class Rtplan():
	def __init__(self,sett,rtplan_dicom):
		'''
		This class parses an RTplan dicom object into a series of segments that can be fed to GPUMCD.

		Some terminology: a controlpoint is a snapshot of the accelerator state at a given point. A Segment is a 'unit' of irradiation associated with a beamweight. Typically this will be the space between two controlpoints: the beamweight is the difference between the cumulative meterset weight and the controlpoint-pair describes the initial and final state of the machine for this segment. Not that Pinnacle has it's own method of interpolation, as it cannot handle dynamic segments during dose calculation.

		Typically, N controlpoints result in N-1 segments.

		Although I could not find an explicit statement on the subject, all spatial distances are returned in units of mm by pydicom. We therefore convert mm to cm. Implicit proof:
		https://pydicom.github.io/pydicom/stable/auto_examples/input_output/plot_read_rtplan.html
		'''
		scale = 0.1 #mm to cm
		assert(isinstance(sett,Settings))
		assert(isinstance(rtplan_dicom,dicom.pydicom_object))

		self.accelerator = Accelerator(sett,rtplan_dicom.data.BeamSequence[0].TreatmentMachineName,rtplan_dicom.data.BeamSequence[0].ControlPointSequence[0].NominalBeamEnergy)
		self.NumberOfFractionsPlanned = rtplan_dicom.NumberOfFractionsPlanned
		self.BeamDose = rtplan_dicom.BeamDose
		self.BeamDoseSpecificationPoint = rtplan_dicom.BeamDoseSpecificationPoint

		self.sett = sett
		firstsegmentonly = False
		if sett.debug['verbose']>0:
			print(self.accelerator)

		self.beamweights = []
		for b in range(rtplan_dicom.NumberOfBeams):
			#theres only 1 fractiongroup
			self.beamweights.append(float(rtplan_dicom.data.FractionGroupSequence[0].ReferencedBeamSequence[b].BeamMeterset))

		self.beams=[] #for each beam, controlpoints
		for bi,bw in enumerate(self.beamweights):
			# total weight of cps in beam is 1
			# convert cumulative weights to relative weights and then absolute weights using bw.
			# https://dicom.innolitics.com/ciods/rt-plan/rt-beams/300a00b0/300a00b6/300a00b8

			nbcps = rtplan_dicom.data.BeamSequence[bi].NumberOfControlPoints
			nsegments = (nbcps-1)
			if firstsegmentonly:
				nsegments = 1
				if bi > 0:
					break

			mlcx_index = None
			mlcy_index = None
			asymy_index = None
			asymx_index = None
			for bld_index in range(len(rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence)):
				thistype = rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence[bld_index].RTBeamLimitingDeviceType
				if "MLCX" == thistype:
					mlcx_index = bld_index
				elif "ASYMY" == thistype or "Y" == thistype:
					asymy_index = bld_index
				elif "ASYMX" == thistype or "X" == thistype:
					asymx_index = bld_index
				elif "MLCY" == thistype:
					mlcy_index = bld_index

			if mlcx_index != None and mlcy_index != None:
				raise NotImplementedError("This plan has BOTH an MLCX and MLCY, which is not implemented.")

			# TODO check if the above matches Accelerator().
			assert(mlcy_index == None)

			#following only available in first cp
			isoCenter = [coor*scale for coor in rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].IsocenterPosition]
			couchAngle = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].PatientSupportAngle #or TableTopEccentricAngle?
			collimatorAngle = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[0].BeamLimitingDeviceAngle

			# N cps = N-1 segments
			self.beams.append(make_c_array(Segment,nsegments))

			for cpi in range(nsegments):
				cp_this = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[cpi]
				cp_next = rtplan_dicom.data.BeamSequence[bi].ControlPointSequence[cpi+1]

				self.beams[bi][cpi] = Segment()

				if asymy_index is None:
					self.beams[bi][cpi].collimator.perpendicularJaw.orientation = ModifierOrientation(-1)
				else:
					self.beams[bi][cpi].collimator.perpendicularJaw.orientation = ModifierOrientation(1)

				if asymx_index is None or self.accelerator.parallelJaw is False:
					self.beams[bi][cpi].collimator.parallelJaw.orientation = ModifierOrientation(-1)
				else:
					self.beams[bi][cpi].collimator.parallelJaw.orientation = ModifierOrientation(0)

				self.beams[bi][cpi].collimator.mlc = MlcInformation(self.accelerator.leafs_per_bank)
				if mlcx_index is None:
					print("No MLC in this CPI, setting it up to match jaw bounds")
				self.beams[bi][cpi].collimator.mlc.orientation = ModifierOrientation(0)

				# Now, let's see what our dicom gives us about this beam

				#following only available in first cp
				self.beams[bi][cpi].beamInfo.isoCenter = Float3(*isoCenter)
				self.beams[bi][cpi].beamInfo.couchAngle = Pair(couchAngle)
				self.beams[bi][cpi].beamInfo.collimatorAngle = Pair(collimatorAngle)

				self.beams[bi][cpi].beamInfo.relativeWeight = (cp_next.CumulativeMetersetWeight-cp_this.CumulativeMetersetWeight) * bw

				#the final CPI may only have a weight and nothing else. Therefore, any other data we retrieve from cp_next, under a try()

				try:
					self.beams[bi][cpi].beamInfo.gantryAngle = Pair(cp_this.GantryAngle,cp_next.GantryAngle)
				except:
					self.beams[bi][cpi].beamInfo.gantryAngle = Pair(cp_this.GantryAngle,cp_this.GantryAngle)
					cp_next = cp_this

				# MLCX
				mlcx_r = []
				mlcx_l = []
				if mlcx_index is not None:
					try:
						for l in range(self.accelerator.leafs_per_bank):
							# leftleaves: eerste helft.
							lval = cp_this.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l]*scale
							rval = cp_this.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale
							lval_next = cp_next.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l]*scale
							rval_next = cp_next.BeamLimitingDevicePositionSequence[mlcx_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale

							self.beams[bi][cpi].collimator.mlc.rightLeaves[l] = Pair(rval,rval_next)
							self.beams[bi][cpi].collimator.mlc.leftLeaves[l] = Pair(lval,lval_next)

							mlcx_r.extend([rval,rval_next])
							mlcx_l.extend([lval,lval_next])
					except Exception as e:# IndexError as e:
						print(f"There was an parsing this RTPlan, aborting...")
						if sett.debug['verbose']>0:
							print(self.accelerator)
							print(f"Filename: {rtplan_dicom.filename}")
							print(f"Beamindex: {bi}")
							print(f"controlpointindex: {cpi}")
							print(f"mlcx_index: {mlcx_index}")
							print(cp_this)
							print(dir(cp_this))
							print(cp_next)
							print(dir(cp_next))
							print(e)
						raise e
				else:
					for l in range(self.accelerator.leafs_per_bank):

						rval = cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale
						rval_next = cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale
						lval = cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale
						lval_next = cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale

						self.beams[bi][cpi].collimator.mlc.rightLeaves[l] = Pair(rval,rval_next)
						self.beams[bi][cpi].collimator.mlc.leftLeaves[l] = Pair(lval,lval_next)

						mlcx_r.extend([rval,rval_next])
						mlcx_l.extend([lval,lval_next])
					# No MLC in CPI, but ofc MLC must be set correctly.


				# prep for field extremeties
				self.beams[bi][cpi].beamInfo.fieldMin = Pair()
				self.beams[bi][cpi].beamInfo.fieldMax = Pair()

				#parallelJaw. may be present in plan, even if accelerator doesnt have it.
				# if self.beams[bi][cpi].collimator.parallelJaw.orientation.value != -1:
				if asymx_index is not None:
					self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale)
					# x coords of field size
					self.beams[bi][cpi].beamInfo.fieldMin.first = min(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].beamInfo.fieldMax.first = max(cp_this.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymx_index].LeafJawPositions[1]*scale)
				else:
					#if no paralleljaw, then we must get extreme field borders from MLCX
					raise NotImplementedError("For missing ASYMX, we need to find leaf extrema within ASYMY bounds. This has not been implemented yet.")
					# self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(min(mlcx_l)*scale)
					# self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(max(mlcx_r)*scale)
					# self.beams[bi][cpi].beamInfo.fieldMax.first = min(mlcx_l)
					# self.beams[bi][cpi].beamInfo.fieldMin.first = max(mlcx_r)

				# perpendicularJaw
				if asymy_index is not None:
					self.beams[bi][cpi].collimator.perpendicularJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].collimator.perpendicularJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale)
					# y coords of fieldsize
					self.beams[bi][cpi].beamInfo.fieldMin.second = min(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].beamInfo.fieldMax.second = max(cp_this.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[asymy_index].LeafJawPositions[1]*scale)
				else:
					#if no perpendicularjaw, then what?
					raise NotImplementedError("No ASYMY jaw found in dicom.")

				# apply field margins
				self.beams[bi][cpi].beamInfo.fieldMin.first -= self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMin.second -= self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMax.first += self.sett.dose['field_margin']*scale
				self.beams[bi][cpi].beamInfo.fieldMax.second += self.sett.dose['field_margin']*scale


		if sett.debug['verbose']>0:
			sumweights=0
			for beam in self.beams:
				beamweight=0
				for segment in beam:
					sumweights+=segment.beamInfo.relativeWeight
					beamweight+=segment.beamInfo.relativeWeight
				print(f"beamweight {beamweight}")
			print(f"total weight {sumweights}")