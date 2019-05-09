import ctypes,numpy as np,os,math,time
import gpumcd
from os import path
import image

sett = gpumcd.Settings("D:\\postdoc\\gpumcd_data")
print(sett.subdirectories['hounsfield_conversion_dir'])
print(sett.__dict__)
quit()

outputdir = "D:\\postdoc\\analyses\\gpumcd_python"


print('Start of program.')

hu2dens_table=[[],[]]
with open(path.join(gpumcd_datadir,'hounsfield','hu2dens.ini'),'r') as f:
	for line in f.readlines():
		if line.startswith('#'):
			continue
		hu2dens_table[0].append(float(line.split()[0]))
		hu2dens_table[1].append(float(line.split()[1]))
dens2mat_table=[[],[]]
with open(path.join(gpumcd_datadir,'hounsfield','dens2mat.ini'),'r') as f:
	for line in f.readlines():
		if line.startswith('#'):
			continue
		dens2mat_table[0].append(float(line.split()[0]))
		dens2mat_table[1].append(line.split()[1])

dens=image.image(path.join(outputdir,'ct.xdr'))
dens.ct_to_hu(-1000,1)
dens.hu_to_density(hu2dens_table)
med=dens.copy()
materials = med.density_to_materialindex(dens2mat_table)
dens.saveas(path.join(outputdir,'dens.xdr'))
med.saveas(path.join(outputdir,'med.xdr'))

phantom=gpumcd.Phantom(massDensityArray_image=dens,mediumIndexArray_image=med)


dose = image.image(DimSize=med.header['DimSize'], ElementSpacing=med.header['ElementSpacing'], Offset=med.header['Offset'], dt='<f4')

physicsSettings = gpumcd.PhysicsSettings()
planSettings = gpumcd.PlanSettings()

physicsSettings.photonTransportCutoff = 0.01
physicsSettings.electronTransportCutoff = 0.189
physicsSettings.inputMaxStepLength = 0.75
physicsSettings.magneticField = gpumcd.Float3(0,0,0)
physicsSettings.referenceMedium = -1
physicsSettings.useElectronInAirSpeedup = 1
physicsSettings.electronInAirSpeedupDensityThreshold = 0.002

planSettings.goalSfom = 2
planSettings.statThreshold = 0.5
planSettings.maxNumParticles = int(1e13)
planSettings.densityThresholdSfom = 0.2
planSettings.densityThresholdOutput = 0.0472
planSettings.useApproximateStatistics = 1

lasterror=ctypes.create_string_buffer(1000)

print('Scene definition loaded.')

Engine = gpumcd.__gpumcd__(path.join(gpumcd_datadir,"dll"))

print('libgpumcd loaded, starting gpumcd init...')

max_streams = math.floor(Engine.get_available_vram(gpu_hardware_id)/Engine.estimate_vram_consumption(phantom.numVoxels.x*phantom.numVoxels.y*phantom.numVoxels.z))
n_streams = min(max_streams,3)

## TODO libgpumcd.initGpumcd.argtypes = ([c_char_p, c_int, c_char_p] etc etc

start_time = time.time()

print(type(ctypes.byref(lasterror)))

retval = Engine.init(
	gpu_hardware_id,
	0,
	gpumcd.str2charp("D:/postdoc/gpumcd_data/materials_clin"),
	*gpumcd.strlist2charpp(materials),
	physicsSettings,
	phantom,
	gpumcd.str2charp("D:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"),
	n_streams,
	ctypes.byref(lasterror)
)

print('gpumcd init done.')

print(retval,lasterror.value.decode('utf-8'))

frame1size = 5
frame2size = 5

BeamFrames = gpumcd.make_c_array(gpumcd.BeamFrame,2)
BeamFrames[0]=gpumcd.BeamFrame(1)
BeamFrames[0].beamInfo[0].relativeWeight = 50
BeamFrames[0].beamInfo[0].isoCenter.x=0
BeamFrames[0].beamInfo[0].isoCenter.y=-20#its below the back, so lets pull it up inside the patient
BeamFrames[0].beamInfo[0].isoCenter.z=0
BeamFrames[0].beamInfo[0].collimatorAngle.first=0
BeamFrames[0].beamInfo[0].collimatorAngle.second=0
BeamFrames[0].beamInfo[0].couchAngle.first=0
BeamFrames[0].beamInfo[0].couchAngle.second=0
BeamFrames[0].beamInfo[0].gantryAngle.first=0
BeamFrames[0].beamInfo[0].gantryAngle.second=0
BeamFrames[0].beamInfo[0].fieldMax.first=frame1size
BeamFrames[0].beamInfo[0].fieldMax.second=frame1size
BeamFrames[0].beamInfo[0].fieldMin.first=-frame1size
BeamFrames[0].beamInfo[0].fieldMin.second=-frame1size
BeamFrames[1]=gpumcd.BeamFrame(1)
BeamFrames[1].beamInfo[0].relativeWeight = 50
BeamFrames[1].beamInfo[0].isoCenter.x=0
BeamFrames[1].beamInfo[0].isoCenter.y=-20
BeamFrames[1].beamInfo[0].isoCenter.z=0
BeamFrames[1].beamInfo[0].collimatorAngle.first=0
BeamFrames[1].beamInfo[0].collimatorAngle.second=0
BeamFrames[1].beamInfo[0].couchAngle.first=0
BeamFrames[1].beamInfo[0].couchAngle.second=0
BeamFrames[1].beamInfo[0].gantryAngle.first=90
BeamFrames[1].beamInfo[0].gantryAngle.second=90
BeamFrames[1].beamInfo[0].fieldMax.first=frame2size
BeamFrames[1].beamInfo[0].fieldMax.second=frame2size
BeamFrames[1].beamInfo[0].fieldMin.first=-frame2size
BeamFrames[1].beamInfo[0].fieldMin.second=-frame2size

print('executing simulation...')

retval = Engine.execute_beamlets(
	*gpumcd.c_array_to_pointer(BeamFrames,True),
	planSettings
)

print(retval)

end_time = time.time()

print("runtime gpumcd:",end_time-start_time)

Engine.get_dose(dose.get_ctypes_pointer_to_data())

dose.saveas(path.join(outputdir,'dose.xdr'))
dose.saveas(path.join(outputdir,'dose.mhd'))