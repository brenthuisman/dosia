import ctypes,numpy as np,os
import gpumcd
from os import path
import image

outputdir = "c:\\postdoc\\analyses\\gpumcd_python"

print('Start of program.')


materials=["Water"]

physicsSettings = gpumcd.PhysicsSettings()
planSettings = gpumcd.PlanSettings()

physicsSettings.photonTransportCutoff = 0.01
physicsSettings.electronTransportCutoff = 0.189
physicsSettings.inputMaxStepLength = 0.75
physicsSettings.magneticField = gpumcd.Float3(0,0,0)
physicsSettings.referenceMedium = -1
physicsSettings.useElectronInAirSpeedup = 1
physicsSettings.electronInAirSpeedupDensityThreshold = 0.002

planSettings.goalSfom = 1
planSettings.statThreshold = 0.5
planSettings.maxNumParticles = int(1e13)
planSettings.densityThresholdSfom = 0.2
planSettings.densityThresholdOutput = 0.0472
planSettings.useApproximateStatistics = 1

phantom = gpumcd.Phantom(50*50*50)
phantom.numVoxels.x = 50
phantom.numVoxels.y = 50
phantom.numVoxels.z = 50

phantom.voxelSizes.x = 0.2
phantom.voxelSizes.y = 0.2
phantom.voxelSizes.z = 0.2

phantom.phantomCorner.x = -5.0
phantom.phantomCorner.y = -5.0
phantom.phantomCorner.z = -5.0

nvox = phantom.numVoxels.x*phantom.numVoxels.y*phantom.numVoxels.z
for i in range(nvox):
	phantom.massDensityArray[i]=1
	phantom.mediumIndexArray[i]=0

lasterror=ctypes.create_string_buffer(1000)

print('Scene definition loaded.')

Engine = gpumcd.__gpumcd__("c:/postdoc/gpumcd_data/dll")

print('libgpumcd loaded, starting gpumcd init...')

print("Engine.get_available_vram(0)",Engine.get_available_vram(0))
print("Engine.estimate_vram_consumption(nvox)",Engine.estimate_vram_consumption(nvox))

n_streams = 1

retval = Engine.init(
	0,
	0,
	gpumcd.str2charp("c:/postdoc/gpumcd_data/materials_clin"),
	*gpumcd.strlist2charpp(materials),
	physicsSettings,
	phantom,
	gpumcd.str2charp("c:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"),
	n_streams,
	ctypes.byref(lasterror)
)

print('gpumcd init done.')

print(retval,lasterror.value.decode('utf-8'))

BeamFrames = gpumcd.make_c_array(gpumcd.BeamFrame,2)
BeamFrames[0]=gpumcd.BeamFrame(1)
BeamFrames[0].beamInfo[0].relativeWeight = 100
BeamFrames[0].beamInfo[0].isoCenter.x=0
BeamFrames[0].beamInfo[0].isoCenter.y=0
BeamFrames[0].beamInfo[0].isoCenter.z=0
BeamFrames[0].beamInfo[0].collimatorAngle.first=0
BeamFrames[0].beamInfo[0].collimatorAngle.second=0
BeamFrames[0].beamInfo[0].couchAngle.first=0
BeamFrames[0].beamInfo[0].couchAngle.second=0
BeamFrames[0].beamInfo[0].gantryAngle.first=0
BeamFrames[0].beamInfo[0].gantryAngle.second=0
BeamFrames[0].beamInfo[0].fieldMax.first=2
BeamFrames[0].beamInfo[0].fieldMax.second=2
BeamFrames[0].beamInfo[0].fieldMin.first=-2
BeamFrames[0].beamInfo[0].fieldMin.second=-2
BeamFrames[1]=gpumcd.BeamFrame(1)
BeamFrames[1].beamInfo[0].relativeWeight = 100
BeamFrames[1].beamInfo[0].isoCenter.x=0
BeamFrames[1].beamInfo[0].isoCenter.y=0
BeamFrames[1].beamInfo[0].isoCenter.z=0
BeamFrames[1].beamInfo[0].collimatorAngle.first=0
BeamFrames[1].beamInfo[0].collimatorAngle.second=0
BeamFrames[1].beamInfo[0].couchAngle.first=0
BeamFrames[1].beamInfo[0].couchAngle.second=0
BeamFrames[1].beamInfo[0].gantryAngle.first=90
BeamFrames[1].beamInfo[0].gantryAngle.second=90
BeamFrames[1].beamInfo[0].fieldMax.first=1
BeamFrames[1].beamInfo[0].fieldMax.second=1
BeamFrames[1].beamInfo[0].fieldMin.first=-1
BeamFrames[1].beamInfo[0].fieldMin.second=-1

print('executing simulation...')

retval = Engine.execute_beamlets(
	*gpumcd.c_array_to_pointer(BeamFrames,True),
	planSettings
)

print(retval)

dose = image.image(DimSize=[50,50,50], ElementSpacing=[0.2,0.2,0.2], dt='<f4')

Engine.get_dose(dose.get_ctypes_pointer_to_data())

dose.saveas(path.join(outputdir,'dose.xdr'))
dose.saveas(path.join(outputdir,'dose.mhd'))