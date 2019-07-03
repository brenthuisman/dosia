import ctypes,numpy as np,os,math,time
from os import path
import gpumcd,image

print('Start of program.')

sett = gpumcd.Settings("c:\\postdoc\\gpumcd_data")
print(sett.planSettings.goalSfom)

casedir = "c:\\postdoc\\analyses\\gpumcd_python"

ct_image=image.image(path.join(casedir,'ct.xdr'))
ct_image.ct_to_hu(1000,1)
ct_image.resample([3,3,3])

ct = gpumcd.CT(sett,ct_image) #for dicoms, dont set intercept,slope.



# TODO RTbeam

machfile = "c:/postdoc/gpumcd_data/machines/machine_van_sami/brentAgility.beamlets.gpumdt"

engine = gpumcd.Engine(sett,ct,machfile)

print('gpumcd init done.')

print (engine.lasterror())

start_time = time.time()



frame1size = 5
frame2size = 3

BeamFrames = gpumcd.make_c_array(gpumcd.BeamFrame,2)
BeamFrames[0]=gpumcd.BeamFrame(1)
BeamFrames[0].beamInfo[0].relativeWeight = 50
BeamFrames[0].beamInfo[0].isoCenter.x=0
BeamFrames[0].beamInfo[0].isoCenter.y=-20 #its below the back, so lets pull it up inside the patient
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

retval = engine.__gpumcd_object__.execute_beamlets(
	*gpumcd.c_array_to_pointer(BeamFrames,True),
	sett.planSettings
)

end_time = time.time()

print (engine.lasterror())

print("runtime gpumcd:",end_time-start_time)

engine.get_dose(ct.dosemap)

ct.dosemap.saveas(path.join(casedir,'dose.xdr'))
ct.dosemap.saveas(path.join(casedir,'dose.mhd'))