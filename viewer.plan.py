from gui import *
import numpy as np
import dicom,gpumcd

class app_frame(Frame):
	def __init__(self, master):
		Frame.__init__(self, master)
		self.grid(row=0, column=0, sticky=NSEW)
		#main window has 1 frame, thats it
		Grid.rowconfigure(master, 0, weight=1)
		Grid.columnconfigure(master, 0, weight=1)
		self.opendicomobject = None

		#swithin that, frames, row-wise, which are updated as necesary.
		#topbar: open file button, contextual info/options
		#main: main viewer. cut into four frames?

		self.new_window(self.topbar_frame(), self.blank_frame())

		return

	def topbar_frame(self,chosen_file=None):

		subframe = Frame(self)

		def newfile():
			if self.opendicomobject.modality == "RTPLAN":
				self.plan = gpumcd.Rtplan(gpumcd.Settings(),self.opendicomobject)
				self.new_window(self.plan_nav(), self.plan_viewer())
			if self.opendicomobject.modality in ["RTDOSE","CT"]:
				self.new_window(self.topbar_image(), self.image_viewer())

		def pickdir():
			self.opendicomobject = dicom.pydicom_object(str(filedialog.askdirectory()))
			newfile()
		def pickfile():
			self.opendicomobject = dicom.pydicom_object(str(filedialog.askopenfilename()))
			newfile()

		Button(subframe, text="Open directory", command=pickdir).pack(side='left')
		Button(subframe, text="Open file", command=pickfile).pack(side='left')

		return subframe


	def plan_nav(self):

		subframe = Frame(self)
		# TODO nav beams, cpis
		# take .first of each segment, and then recreate last cpi by taking .second of the last segment.

		return subframe

	def new_window(self,t,m):
		#swithin that, frames, row-wise, which are updated as necesary.
		#topbar: displays stage of verification
		#middle screen shows options or info
		#bottom bar shows actions

		for rows in range(2):
			Grid.rowconfigure(self, rows, weight=1)
		for columns in range(1):
			Grid.columnconfigure(self, columns, weight=1)

		Grid.rowconfigure(self, 0, weight=0) #override weight: sets size to minimal size
		self.topbar = t
		self.topbar.grid(row=0, column=0, sticky=N+S+E+W,padx=20,pady=(20,0))

		Grid.columnconfigure(self, 2, weight=0)
		self.mainframe = m
		self.mainframe.grid(row=2, column=0, sticky=N+S+E+W,padx=20,pady=20)
		return

	def plan_viewer(self,beami=0,segmenti=0):
		subframe = Frame(self)

		#800x800
		vert_zoom= 20
		canvas = Canvas(subframe)
		canvas.configure(width=800, height=800)
		# canvas.create_line(15, 25, 200, 25)
		# canvas.create_line(300, 35, 300, 200, dash=(4, 2))
		# canvas.create_line(55, 85, 155, 85, 105, 180, 55, 85)

		leafedges = np.linspace(0,800,self.plan.accelerator.leafs_per_bank+1)

		for l in range(self.plan.accelerator.leafs_per_bank):
			bound1 = leafedges[l]
			bound2 = leafedges[l+1]

			#left
			coord = vert_zoom * self.plan.beams[beami][segmenti].collimator.mlc.leftLeaves[l].first
			canvas.create_line(400+coord, bound1, 400+coord, bound2)
			canvas.create_line(400+coord-50, bound1, 400+coord, bound1)
			canvas.create_line(400+coord-50, bound2, 400+coord, bound2)

			#right
			coord = vert_zoom * self.plan.beams[beami][segmenti].collimator.mlc.rightLeaves[l].first
			canvas.create_line(400+coord, bound1, 400+coord, bound2,fill="blue")
			canvas.create_line(400+coord+50, bound1, 400+coord, bound1,fill="blue")
			canvas.create_line(400+coord+50, bound2, 400+coord, bound2,fill="blue")

			#jaws
			l,r = vert_zoom* self.plan.beams[beami][segmenti].collimator.parallelJaw.j1.first, vert_zoom * self.plan.beams[beami][segmenti].collimator.parallelJaw.j2.first
			canvas.create_line(400+l, 0, 400+l, 800,fill='black')
			canvas.create_line(400+r, 0, 400+r, 800,fill='blue')

			t,b = vert_zoom* self.plan.beams[beami][segmenti].collimator.perpendicularJaw.j1.first, vert_zoom * self.plan.beams[beami][segmenti].collimator.perpendicularJaw.j2.first
			canvas.create_line(0, 400+t, 800, 400+t,fill='yellow')
			canvas.create_line(0, 400+b, 800, 400+b,fill='green')

			# fieldsize
			x1,x2 = vert_zoom* self.plan.beams[beami][segmenti].beamInfo.fieldMin.first, vert_zoom * self.plan.beams[beami][segmenti].beamInfo.fieldMax.first
			y1,y2 = vert_zoom* self.plan.beams[beami][segmenti].beamInfo.fieldMin.second, vert_zoom * self.plan.beams[beami][segmenti].beamInfo.fieldMax.second
			canvas.create_line(400+x1, 400+y1, 400+x1, 400+y2,fill='red')
			canvas.create_line(400+x1, 400+y1, 400+x2, 400+y1,fill='red')
			canvas.create_line(400+x1, 400+y2, 400+x2, 400+y2,fill='red')
			canvas.create_line(400+x2, 400+y1, 400+x2, 400+y2,fill='red')






		canvas.pack()#fill=BOTH, expand=1)

		return subframe



	def blank_frame(self):
		subframe = Frame(self)
		return subframe

def main():
	root = Tk()
	app = app_frame(root)

	w = 800 # width for the Tk root
	h = 900 # height for the Tk root

	# get screen width and height
	ws = root.winfo_screenwidth() # width of the screen
	hs = root.winfo_screenheight() # height of the screen

	# calculate x and y coordinates for the Tk root window
	x = (ws/2) - (w/2)
	y = (hs/2) - (h/2)

	# set the dimensions of the screen
	# and where it is placed
	root.geometry('%dx%d+%d+%d' % (w, h, x, y))
	root.wm_title("Brent's viewer")

	root.mainloop()

	# if app.p2d.len_all_err>0:
	# 	return 1
	# else:
	# 	return 0

if __name__ == "__main__":
	main()

