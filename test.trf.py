import trf

fn=r"D:\postdoc\analyses\trf\19_03_27 13_28_48 Z 1_210_1_210.trf"

header,table=trf.read_trf(fn)
print(header)
print("================")
print(table)

header.to_csv(r"D:\postdoc\analyses\trf\trfhead.csv")
table.to_csv(r"D:\postdoc\analyses\trf\trftab.csv")