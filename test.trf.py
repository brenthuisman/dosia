import trf
from gpumcd.ctypes_helpers import make_c_array
from gpumcd.gpumcdwrapper import Segment, Pair, MlcInformation, ModifierOrientation, Float3

fn=r"D:\postdoc\analyses\trf\19_03_27 13_28_48 Z 1_210_1_210.trf"

header,table=trf.read_trf(fn)
#table.to_csv(r"D:\postdoc\analyses\trf\trftab.csv")

table = table[table["Linac State/Actual Value (None)"] == "Radiation On"]

#table.to_csv(r"D:\postdoc\analyses\trf\trfcondsensed.csv")

nsegments = len(table)

for index,row in table.iterrows():
	if row["Linac State/Actual Value (None)"] == "Radiation On":
		nsegments += 1

print(f"{nsegments} snapshots found.")
segments = make_c_array(Segment,nsegments)

for index,row in table.iterrows():
	segments[index]=Segment()
	segments[index].collimator.perpendicularJaw
