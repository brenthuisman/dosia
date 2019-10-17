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

		self.accelerator = Accelerator(rtplan_dicom,sett)
		print(self.accelerator)
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

			mlc_index = None
			perpendicular_index = None
			parallel_index = None # even if not present in accelerator, tps may export it as indication of field bounds

			#now, lets match BeamLimitingDeviceSequence to collimator element
			for bld_index in range(len(rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence)):
				bld_type = str(rtplan_dicom.data.BeamSequence[bi].BeamLimitingDeviceSequence[bld_index].RTBeamLimitingDeviceType)

				if bld_type in self.accelerator.mlcName:
					mlc_index = bld_index
				if bld_type in self.accelerator.perpendicularJawName:
					perpendicular_index = bld_index
				elif bld_type in self.accelerator.parallelJawName:
					parallel_index = bld_index
				else:
					NotImplementedError(f"This plan has an unrecognized collimator element {bld_type}.")

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

				self.beams[bi][cpi].collimator.perpendicularJaw.orientation = self.accelerator.perpendicularJawOrientation
				self.beams[bi][cpi].collimator.parallelJaw.orientation = self.accelerator.parallelJawOrientation
				self.beams[bi][cpi].collimator.mlc = MlcInformation(self.accelerator.leafs_per_bank)
				if mlc_index is None:
					print("No MLC in this CPI, setting it up to match jaw bounds")
				self.beams[bi][cpi].collimator.mlc.orientation = self.accelerator.mlcOrientation

				# Now, let's see what our dicom gives us about this beam

				#following only available in first cp
				self.beams[bi][cpi].beamInfo.isoCenter = Float3(*isoCenter)
				self.beams[bi][cpi].beamInfo.couchAngle = Pair(couchAngle)
				self.beams[bi][cpi].beamInfo.collimatorAngle = Pair(collimatorAngle)

				self.beams[bi][cpi].beamInfo.relativeWeight = (cp_next.CumulativeMetersetWeight-cp_this.CumulativeMetersetWeight) * bw

				#the final CPI may only have a weight and nothing else. It may have a GantryAngle... or not.
				# Therefore, any other data we retrieve from cp_next, under a try()
				try:
					self.beams[bi][cpi].beamInfo.gantryAngle = Pair(cp_this.GantryAngle,cp_next.GantryAngle)
				except:
					self.beams[bi][cpi].beamInfo.gantryAngle = Pair(cp_this.GantryAngle,cp_this.GantryAngle)

				# Test if final cp has BeamLimitingDevicePositionSequence, if not, copy from cp_this
				try:
					cp_next.BeamLimitingDevicePositionSequence[0] #acces first, if not present, must be same as previous
				except:
					cp_next = cp_this

				# MLC
				mlcx_r = []
				mlcx_l = []
				if mlc_index is not None:
					try:
						for l in range(self.accelerator.leafs_per_bank):
							# leftleaves: eerste helft.
							lval = cp_this.BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[l]*scale
							rval = cp_this.BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale
							lval_next = cp_next.BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[l]*scale
							rval_next = cp_next.BeamLimitingDevicePositionSequence[mlc_index].LeafJawPositions[l+self.accelerator.leafs_per_bank]*scale

							self.beams[bi][cpi].collimator.mlc.rightLeaves[l] = Pair(rval,rval_next)
							self.beams[bi][cpi].collimator.mlc.leftLeaves[l] = Pair(lval,lval_next)

							mlcx_r.extend([rval,rval_next])
							mlcx_l.extend([lval,lval_next])
					except Exception as e:# IndexError as e:
						print(f"There was an error parsing this RTPlan, aborting...")
						if sett.debug['verbose']>0:
							print(self.accelerator)
							print(f"Filename: {rtplan_dicom.filename}")
							print(f"Beamindex: {bi}")
							print(f"controlpointindex: {cpi}")
							print(f"mlc_index: {mlc_index}")
							print(cp_this)
							print(dir(cp_this))
							print(cp_next)
							print(dir(cp_next))
							print(e)
						raise e
				else:
					# No MLC in CPI, but ofc MLC must be set correctly.
					for l in range(self.accelerator.leafs_per_bank):

						rval = cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale
						rval_next = cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale
						lval = cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale
						lval_next = cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale

						self.beams[bi][cpi].collimator.mlc.rightLeaves[l] = Pair(rval,rval_next)
						self.beams[bi][cpi].collimator.mlc.leftLeaves[l] = Pair(lval,lval_next)

						mlcx_r.extend([rval,rval_next])
						mlcx_l.extend([lval,lval_next])


				# prep for field extremeties
				self.beams[bi][cpi].beamInfo.fieldMin = Pair()
				self.beams[bi][cpi].beamInfo.fieldMax = Pair()

				#parallelJaw. may be present in plan, even if accelerator doesnt have it.
				# if self.beams[bi][cpi].collimator.parallelJaw.orientation.value != -1:
				if parallel_index is not None:
					self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale)
					# x coords of field size
					self.beams[bi][cpi].beamInfo.fieldMin.first = min(cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].beamInfo.fieldMax.first = max(cp_this.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[parallel_index].LeafJawPositions[1]*scale)
				else:
					print ("No parallelJaw found, taking extremes MLC values as field-edges.")
					#strictly speaking not relevant:
					self.beams[bi][cpi].collimator.parallelJaw.j1 = Pair(min(mlcx_l))
					self.beams[bi][cpi].collimator.parallelJaw.j2 = Pair(max(mlcx_r))
					# but this is:
					self.beams[bi][cpi].beamInfo.fieldMin.first = min(mlcx_l)
					self.beams[bi][cpi].beamInfo.fieldMax.first = max(mlcx_r)
					# FIXME: should really be looking at leafs within ASYMY bounds

				# perpendicularJaw
				if perpendicular_index is not None:
					self.beams[bi][cpi].collimator.perpendicularJaw.j1 = Pair(cp_this.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].collimator.perpendicularJaw.j2 = Pair(cp_this.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[1]*scale)
					# y coords of fieldsize
					self.beams[bi][cpi].beamInfo.fieldMin.second = min(cp_this.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[0]*scale,cp_next.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[0]*scale)
					self.beams[bi][cpi].beamInfo.fieldMax.second = max(cp_this.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[1]*scale,cp_next.BeamLimitingDevicePositionSequence[perpendicular_index].LeafJawPositions[1]*scale)
				else:
					#if no perpendicularjaw, then what?
					NotImplementedError(f"No perpendicularJaw found in controlpoint {cpi} of beam {bi}.")

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