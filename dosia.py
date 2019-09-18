#!/usr/bin/python3

import medimage as image, dicom, gpumcd, numpy as np
from gui import *

# todo: load this from an ini? gui setting?
sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

class ImagePane(QWidget):
	def __init__(self, fname, *args,**kwargs):
		super().__init__(*args,**kwargs)

		self.image = image.image(fname)

		x,y,z=self.image.get_slices_at_index()
		# import scipy.misc
		# scipy.misc.imsave("d:/slicex.png",x)
		# scipy.misc.imsave("d:/slicey.png",y)
		# scipy.misc.imsave("d:/slicez.png",z)
		x=np.interp(x, (x.min(), x.max()), (0, 255))
		im = np.copy(np.rot90(np.rot90(np.uint8(x).T)),order='C')
		self.qimage = QImage(im,im.shape[1],im.shape[0],QImage.Format_Grayscale8)

	def paintEvent(self,e):
		painter = QPainter(self)
		painter.drawPixmap(self.rect(), QPixmap(self.qimage))
		# i=image.image(DimSize=[1,1],ElementSpacing=[1,1])
		# a=QPixmap()
		# a.loadFromData(i.get_ctypes_pointer_to_data(self.im))
		# painter.drawPixmap(self.rect(), QPixmap(a))

	def minimumSizeHint(self):
		return QSize(200, 200)


class PlanPane(QWidget):
	def __init__(self, fname, *args,**kwargs):
		super().__init__(*args,**kwargs)

		opendicomobject = dicom.pydicom_object(fname)
		if opendicomobject.modality == "RTPLAN":
			self.plan = gpumcd.Rtplan(sett,opendicomobject)
		else:
			IOError("That aint no dicom plan, mister!")

		self.bi=0
		self.si=0
		self.be=0

		self.beam_slider = BSlider("Beam index",0,len(self.plan.beams)-1,self.setbi)
		self.segment_slider = BSlider("Segment index",0,len(self.plan.beams[0])-1,self.setsi)
		self.beginend_slider = BSlider("Seg. Position","Begin","End",self.setbe)

		l = QVBoxLayout()
		self.canvas = PlanCanvas(self.plan)

		planNav = QHBoxLayout()
		planNav.setContentsMargins(0, 0, 0, 0)
		# stretchfactor are integers
		planNav.addWidget(self.beam_slider,0)
		planNav.addWidget(self.segment_slider,1)
		planNav.addWidget(self.beginend_slider,0)

		l.addLayout(planNav,0)
		l.addWidget(self.canvas,1)

		self.setLayout(l)

		self.canvas.setFrame(self.bi,self.si,self.be)

	def setbi(self,v):
		self.bi=v
		self.canvas.setFrame(self.bi,self.si,self.be)

	def setsi(self,v):
		self.si=v
		self.canvas.setFrame(self.bi,self.si,self.be)

	def setbe(self,v):
		self.be=v
		self.canvas.setFrame(self.bi,self.si,self.be)


class PlanCanvas(QWidget):
	def __init__(self, plan, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.plan = plan
		self.si = 0
		self.bi = 0
		self.be = 0

	def setFrame(self, bi, si ,be):
		self.si = si
		self.bi = bi
		self.be = be
		self.update()

	def minimumSizeHint(self):
		return QSize(200, 200)

	def paintEvent(self,e):
		try:
			plan = self.plan
			segment = self.plan.beams[self.bi][self.si]
		except:
			print("Tried to paint a plan, but no plan was loaded.")
			return
		attr="second"
		if self.be==0:
			attr="first"
		w=self.width()#/800
		h=self.height()#/800
		# print(w,h)

		qp = QPainter()
		qp.begin(self)
		pen = QPen(Qt.black, 2, Qt.SolidLine)

		h400 = h/2 # TEST
		w400 = w/2 # TEST
		vert_zoom= w400 / 400. * 20
		hor_zoom= h400 / 400. * 20
		leafedges = np.linspace(0,h,plan.accelerator.leafs_per_bank+1)

		for l in range(plan.accelerator.leafs_per_bank):
			bound1 = leafedges[l]
			bound2 = leafedges[l+1]

			#left
			coord = vert_zoom * getattr(segment.collimator.mlc.leftLeaves[l],attr)
			pen.setColor(Qt.green)
			qp.setPen(pen)
			qp.drawLine(w400+coord, bound1, w400+coord, bound2)
			qp.drawLine(w400+coord-50, bound1, w400+coord, bound1,)
			qp.drawLine(w400+coord-50, bound2, w400+coord, bound2)

			#right
			coord = vert_zoom * getattr(segment.collimator.mlc.rightLeaves[l],attr)
			pen.setColor(Qt.blue)
			qp.setPen(pen)
			qp.drawLine(w400+coord, bound1, w400+coord, bound2)
			qp.drawLine(w400+coord+50, bound1, w400+coord, bound1)
			qp.drawLine(w400+coord+50, bound2, w400+coord, bound2)

		if segment.collimator.parallelJaw.orientation.value == -1:
			pen.setStyle(Qt.DashLine)
		else:
			pass

		#jaws
		l,r = vert_zoom* getattr(segment.collimator.parallelJaw.j1,attr), vert_zoom * getattr(segment.collimator.parallelJaw.j2,attr)

		pen.setColor(Qt.green)
		pen.setWidth(2)
		qp.setPen(pen)
		qp.drawLine(w400+l, 0, w400+l, h)

		pen.setColor(Qt.blue)
		qp.drawLine(w400+r, 0, w400+r, h)

		t,b = hor_zoom* getattr(segment.collimator.perpendicularJaw.j1,attr), hor_zoom * getattr(segment.collimator.perpendicularJaw.j2,attr)

		pen.setColor(Qt.cyan)
		pen.setStyle(Qt.SolidLine)
		qp.setPen(pen)
		qp.drawLine(0, h400+t, w, h400+t)
		pen.setColor(Qt.magenta)
		qp.setPen(pen)
		qp.drawLine(0, h400+b, w, h400+b)

		# fieldsize
		x1,x2 = vert_zoom* segment.beamInfo.fieldMin.first, vert_zoom * segment.beamInfo.fieldMax.first
		y1,y2 = hor_zoom* segment.beamInfo.fieldMin.second, hor_zoom * segment.beamInfo.fieldMax.second

		pen.setColor(Qt.red)
		qp.setPen(pen)
		qp.drawLine(w400+x1, h400+y1, w400+x1, h400+y2)
		qp.drawLine(w400+x1, h400+y1, w400+x2, h400+y1)
		qp.drawLine(w400+x1, h400+y2, w400+x2, h400+y2)
		qp.drawLine(w400+x2, h400+y1, w400+x2, h400+y2)

		# canvas_textbox = canvas.create_text(10, 10, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text="viewport: 40cm x 40cm")
		# canvas_textbox = canvas.create_text(10, 25, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text=f"isoCenter: {str(self.plan.beams[beami][0].beamInfo.isoCenter.x)[:5]},{str(self.plan.beams[beami][0].beamInfo.isoCenter.y)[:5]},{str(self.plan.beams[beami][0].beamInfo.isoCenter.z)[:5]}")
		# canvas_textbox = canvas.create_text(10, 40, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text=f"weight: {str(segment.beamInfo.relativeWeight)}")
		# canvas_textbox = canvas.create_text(10, 55, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text=f"gantryAngle: {str(getattr(segment.beamInfo.gantryAngle,attr))}")
		# canvas_textbox = canvas.create_text(10, 70, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text=f"collimatorAngle: {str(getattr(self.plan.beams[beami][0].beamInfo.collimatorAngle,attr))}")
		# canvas_textbox = canvas.create_text(10, 85, anchor="nw")
		# canvas.itemconfig(canvas_textbox, text=f"couchAngle: {str(getattr(self.plan.beams[beami][0].beamInfo.couchAngle,attr))}")


		# qp.end()


class FourPanel(QWidget):
	def __init__(self, tl, tr, bl, br, *args,**kwargs):
		super().__init__(*args,**kwargs)

		mainLayout = QGridLayout()
		mainLayout.addWidget(tl, 0, 0)
		mainLayout.addWidget(tr, 0, 1)
		mainLayout.addWidget(bl, 1, 0)
		mainLayout.addWidget(br, 1, 1)

		# make all panels take up same space (quadrants)
		mainLayout.setRowStretch(0, 1)
		mainLayout.setRowStretch(1, 1)
		mainLayout.setColumnStretch(0, 1)
		mainLayout.setColumnStretch(1, 1)
		self.setLayout(mainLayout)


class DosiaMain(QMainWindow):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.setWindowTitle("Dosia")
		self.resize(800, 800)
		self.move(300, 300)
		self.setWindowIcon(QIcon('gui/audio-card.svg'))

		# Menu bar
		menu_load_file = QAction('&File (RTPlan, Dose, CT)', self)
		menu_load_file.triggered.connect(self.loadfile)
		menu_load_dir = QAction('&Directory (CT)', self)
		menu_load_dir.triggered.connect(self.loaddir)
		# menu_open_linaclog = QAction('&Linac Log', self)
		# menu_open_linaclog.triggered.connect(self.loadlinaclog)
		# menu_open_linaclog.setDisabled(True) #TODO: enable if rtplan loaded

		menu_gpumcd_calculate = QAction('&Calculate Dose', self)
		menu_gpumcd_calculate.triggered.connect(self.calcgpumcd)
		menu_gpumcd_calculate.setDisabled(True) #TODO: enable if rtplan and ct loaded
		menu_gpumcd_save = QAction('&Save Dose', self)
		menu_gpumcd_save.triggered.connect(self.savegpumcd)
		menu_gpumcd_save.setDisabled(True) #TODO: enable if gpumcd dose calculated.

		menu_bar = self.menuBar()
		menu_open = menu_bar.addMenu('&Load')
		menu_open.addAction(menu_load_file)
		menu_open.addAction(menu_load_dir)

		menu_gpumcd = menu_bar.addMenu('&GPUMCD')
		menu_gpumcd.addAction(menu_gpumcd_calculate)
		menu_gpumcd.addAction(menu_gpumcd_save)

		# Quadrants
		self.planpane = QWidget()
		self.plandosepane = QWidget()
		self.ctpane = QWidget()
		self.gpumcdpane = QWidget()
		self.resetpanes()

		# statusbar
		self.statusBar().showMessage('Ready')

		# done!
		self.show()

	def resetpanes(self):
		self.setCentralWidget(FourPanel(self.planpane,self.plandosepane,self.ctpane,self.gpumcdpane))

	#TODO: error handling in loading files

	def loadfile(self):
		fname = str(QFileDialog.getOpenFileName(self, 'Open Dicom file (rtplan, ct or dose)')[0])
		try:
			opendicomobject = dicom.pydicom_object(fname)
			if opendicomobject.modality == "RTPLAN":
				self.planpane = PlanPane(fname)
			if opendicomobject.modality == "CT":
				self.ctpane = ImagePane(fname)
			if opendicomobject.modality == "RTDOSE":
				self.plandosepane = ImagePane(fname)
		except Exception as e:
			self.popup(f"That was not a valid DICOM file.\n{str(e)}")
			return
		self.resetpanes()

	def loaddir(self):
		fname = str(QFileDialog.getExistingDirectory(self, 'Open Dicom CT (slices) directory'))
		try:
			opendicomobject = dicom.pydicom_object(fname)
			assert opendicomobject.modality == "CT", "That directory did not contain a valid set of DICOM CT slices."
			self.ctpane = ImagePane(fname)
		except Exception as e:
			self.popup(f"That was not a valid DICOM file.\n{str(e)}")
			return
		self.resetpanes()

	def loadcase(self):
		# TODO: open dir and search for rtplan,ct,dose and set panes accordingly.
		# multiple rtplan selector?
		pass

	def loadlinaclog(self):
		# fname = str(QFileDialog.getOpenFileName(self, 'Open Dicom Dose')[0])
		# self.topleft = QWidget()#somewidget(fname)
		self.resetpanes()

	def calcgpumcd(self):
		# fname = str(QFileDialog.getOpenFileName(self, 'Open Dicom Dose')[0])
		# self.topleft = QWidget()#somewidget(fname)
		self.resetpanes()
		pass

	def savegpumcd(self):
		fname = str(QFileDialog.getSaveFileName(self, 'Save GPUMCD Dose')[0])
		self.gpumcdpane.save(fname)
		# self.topleft = QWidget()#somewidget(fname)
		# self.setCentralWidget(FourPanel(self.topleft,self.topright,self.bottomleft,self.bottomright))
		pass

	def popup(self,message):
		a = QMessageBox()
		a.setText(message)
		a.exec()
		print(str(message))


if __name__ == '__main__':
	import sys

	app = QApplication(sys.argv)

	# TEST PLAN VIEWER
	# fname="D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/1. UPI263538/2.25.1025001435024675917588954042793107482"
	# opendicomobject = dicom.pydicom_object(fname)
	# p=PlanPane(gpumcd.Rtplan(gpumcd.Settings(),opendicomobject))
	# p.show()

	# TEST CT VIEWER
	# fname = "D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/2. HalsSupracl + C   3.0  B40s PLAN"
	# p=ImagePane(fname)
	# p.show()


	# TEST MAIN
	Main = DosiaMain()

	sys.exit(app.exec())