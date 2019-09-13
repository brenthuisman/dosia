#!/usr/bin/python3

import dicom, gpumcd, image, numpy as np
from gui import *

# todo: load this from an ini?
sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

class CTWidget(QWidget):
	def __init__(self, fname, *args,**kwargs):
		super().__init__(*args,**kwargs)

		opendicomobject = dicom.pydicom_object(fname)
		if opendicomobject.modality == "CT":
			ct = image.image(fname)
		else:
			IOError("That aint no dicom ct!")
		# self.ct = gpumcd.CT(sett,ct)

		x,y,z=ct.get_slices_at_index()
		print(x.max(),x.min())
		print(x.shape,y.shape,z.shape)
		x=x+100
		import scipy.misc
		scipy.misc.imsave("d:/slicex.png",x)
		scipy.misc.imsave("d:/slicey.png",y)
		scipy.misc.imsave("d:/slicez.png",z)
		# x=x.astype(np.uint16)#+x.min()
		# scipy.misc.imsave("d:/slice2.png",np.rot90(x))
		# print(x.max(),x.min())
		im=np.uint8(x)#require(x, np.uint8, 'C')
		print(im.shape[1],im.shape[0])
		print(x.shape[1],x.shape[0])
		self.qimage = QImage(im,im.shape[1],im.shape[0],QImage.Format_Grayscale8)

		self.im=im


	def paintEvent(self,e):
		painter = QPainter(self)
		painter.drawPixmap(self.rect(), QPixmap(self.qimage))
		# i=image.image(DimSize=[1,1],ElementSpacing=[1,1])
		# a=QPixmap()
		# a.loadFromData(i.get_ctypes_pointer_to_data(self.im))
		# painter.drawPixmap(self.rect(), QPixmap(a))

	def minimumSizeHint(self):
		return QSize(200, 200)


class PlanWidget(QWidget):
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

		self.informationButton = QPushButton("wut")
		self.informationButton.clicked.connect(self.informationMessage)
		l.addWidget(self.informationButton,0)
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

	def informationMessage(self):
		a = QMessageBox()
		a.setText(f'haha{self.bi,self.si,self.be}')
		a.exec()


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
		print(w,h)

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

		# Menu bar
		planOpen = QAction('&Plan', self)
		planOpen.triggered.connect(self.setplan)
		ctOpen = QAction('&CT', self)
		ctOpen.triggered.connect(self.setct)

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&Open')
		fileMenu.addAction(planOpen)
		fileMenu.addAction(ctOpen)

		# Qudrants
		self.topleft = QWidget()
		self.topright = QWidget()
		self.bottomleft = QWidget()
		self.bottomright = QWidget()
		self.setCentralWidget(FourPanel(self.topleft,self.topright,self.bottomleft,self.bottomright))

		# statusbar
		self.statusBar().showMessage('Ready')

		# done!
		self.show()

	def setplan(self):
		fname = str(QFileDialog.getOpenFileName(self, 'Open Plan Dicom')[0])
		self.topleft = PlanWidget(fname)
		self.setCentralWidget(FourPanel(self.topleft,self.topright,self.bottomleft,self.bottomright))

	def setct(self):
		# fname = str(QFileDialog.getOpenFileName(self, 'Open CT Dicom')[0])
		fname = str(QFileDialog.getExistingDirectory(self, 'Open CT Dicom'))
		self.topright = CTWidget(fname)
		self.setCentralWidget(FourPanel(self.topleft,self.topright,self.bottomleft,self.bottomright))


if __name__ == '__main__':
	import sys

	app = QApplication(sys.argv)


	# fname="D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/1. UPI263538/2.25.1025001435024675917588954042793107482"
	# opendicomobject = dicom.pydicom_object(fname)
	# p=PlanWidget(gpumcd.Rtplan(gpumcd.Settings(),opendicomobject))
	# p.show()

	fname = "D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/2. HalsSupracl + C   3.0  B40s PLAN"
	p=CTWidget(fname)
	p.show()



	# Main = DosiaMain()
	sys.exit(app.exec())