#!/usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class BSlider(QWidget):
	def __init__(self, title, minval, maxval, slot=None, defval=0, orientation=Qt.Horizontal, parent=None):
		super().__init__(parent)

		self.value = defval

		self.slider = QSlider(orientation,self)
		self.slider.setTickPosition(QSlider.TicksBelow)
		self.slider.setValue(defval)
		self.slider.valueChanged[int].connect(self.changeValue)
		if slot != None:
			self.slider.valueChanged[int].connect(slot)

		self.title = QLabel(title,self)

		if isinstance(minval, str):
			# assume this is a switch with just two values.
			self.slider.setMinimum(0)
			self.slider.setMaximum(1)
			t = QHBoxLayout()
			t.setContentsMargins(0, 0, 0, 0)
			t.addWidget(QLabel(minval,self))
			t.addStretch(1)
			t.addWidget(QLabel(maxval,self))
		else:
			self.slider.setMinimum(minval)
			self.slider.setMaximum(maxval)
			self.vallabel = QLabel(str(defval),self)
			self.vallabel.setAlignment(Qt.AlignCenter)

		l = QVBoxLayout()
		l.setContentsMargins(0, 0, 0, 0)
		l.addWidget(self.title)
		l.addWidget(self.slider)
		if isinstance(minval, str):
			l.addLayout(t)
		else:
			l.addWidget(self.vallabel)

		self.setLayout(l)

	def changeValue(self,v):
		self.value = v
		# print(self.title.text(),v)
		try:
			self.vallabel.setText(str(v))
		except:
			pass


class PlanView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

		self.bi=0
		self.si=0
		self.be=0

		self.beam_slider = BSlider("Beam index",0,2,self.setbi)
		self.segment_slider = BSlider("Segment index",0,20,self.setsi)
		self.beginend_slider = BSlider("Seg. Position","Begin","End",self.setbe)

		l = QVBoxLayout()

		planNav = QHBoxLayout()
		planNav.setContentsMargins(0, 0, 0, 0)
		# stretchfactor are integers
		planNav.addWidget(self.beam_slider,1)
		planNav.addWidget(self.segment_slider,2)
		planNav.addWidget(self.beginend_slider,0)

		l.addLayout(planNav)
		# l.addLayout(planCanvas)


		self.informationButton = QPushButton("wut")
		self.informationButton.clicked.connect(self.informationMessage)
		l.addWidget(self.informationButton)
		self.setLayout(l)

	def setbi(self,v):
		self.bi=v
		print('haha',self.bi,self.si,self.be)

	def setsi(self,v):
		self.si=v
		print('haha',self.bi,self.si,self.be)

	def setbe(self,v):
		self.be=v
		print('haha',self.bi,self.si,self.be)


	def informationMessage(self):
		a = QMessageBox()
		a.setText(f'haha{self.bi,self.si,self.be}')
		a.exec_()




class PlanCanvas(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

	def setframe(self, frame):
		pass

	def paintEvent(self,event):
		pass


	def resizeEvent(self,event):
		pass

	def paint(self):
		wf=self.width()/800
		hf=self.height()/800

		qp = QPainter()
		qp.begin(self)

			# canvas.configure(width=w, height=h)
			# h400 = h/2 # TEST
			# w400 = w/2 # TEST
			# vert_zoom= w400 / 400. * 20
			# hor_zoom= h400 / 400. * 20
			# leafedges = np.linspace(0,h,self.plan.accelerator.leafs_per_bank+1)

			# for l in range(self.plan.accelerator.leafs_per_bank):
			# 	bound1 = leafedges[l]
			# 	bound2 = leafedges[l+1]

			# 	#left
			# 	coord = vert_zoom * getattr(self.plan.beams[beami][segmenti].collimator.mlc.leftLeaves[l],attr)
			# 	canvas.create_line(w400+coord, bound1, w400+coord, bound2,fill="green")
			# 	canvas.create_line(w400+coord-50, bound1, w400+coord, bound1,fill="green")
			# 	canvas.create_line(w400+coord-50, bound2, w400+coord, bound2,fill="green")

			# 	#right
			# 	coord = vert_zoom * getattr(self.plan.beams[beami][segmenti].collimator.mlc.rightLeaves[l],attr)
			# 	canvas.create_line(w400+coord, bound1, w400+coord, bound2,fill="blue")
			# 	canvas.create_line(w400+coord+50, bound1, w400+coord, bound1,fill="blue")
			# 	canvas.create_line(w400+coord+50, bound2, w400+coord, bound2,fill="blue")

			# if self.plan.beams[beami][segmenti].collimator.parallelJaw.orientation.value == -1:
			# 	dash = (4,2)
			# else:
			# 	dash = None

			# #jaws
			# l,r = vert_zoom* getattr(self.plan.beams[beami][segmenti].collimator.parallelJaw.j1,attr), vert_zoom * getattr(self.plan.beams[beami][segmenti].collimator.parallelJaw.j2,attr)
			# canvas.create_line(w400+l, 0, w400+l, h,fill='green', width=2,dash=dash)
			# canvas.create_line(w400+r, 0, w400+r, h,fill='blue', width=2,dash=dash)

			# t,b = hor_zoom* getattr(self.plan.beams[beami][segmenti].collimator.perpendicularJaw.j1,attr), hor_zoom * getattr(self.plan.beams[beami][segmenti].collimator.perpendicularJaw.j2,attr)
			# canvas.create_line(0, h400+t, w, h400+t,fill='orange', width=2)
			# canvas.create_line(0, h400+b, w, h400+b,fill='brown', width=2)

			# # fieldsize
			# x1,x2 = vert_zoom* self.plan.beams[beami][segmenti].beamInfo.fieldMin.first, vert_zoom * self.plan.beams[beami][segmenti].beamInfo.fieldMax.first
			# y1,y2 = hor_zoom* self.plan.beams[beami][segmenti].beamInfo.fieldMin.second, hor_zoom * self.plan.beams[beami][segmenti].beamInfo.fieldMax.second
			# canvas.create_line(w400+x1, h400+y1, w400+x1, h400+y2,fill='red', width=2)
			# canvas.create_line(w400+x1, h400+y1, w400+x2, h400+y1,fill='red', width=2)
			# canvas.create_line(w400+x1, h400+y2, w400+x2, h400+y2,fill='red', width=2)
			# canvas.create_line(w400+x2, h400+y1, w400+x2, h400+y2,fill='red', width=2)

			# canvas_textbox = canvas.create_text(10, 10, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text="viewport: 40cm x 40cm")
			# canvas_textbox = canvas.create_text(10, 25, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text=f"isoCenter: {str(self.plan.beams[beami][0].beamInfo.isoCenter.x)[:5]},{str(self.plan.beams[beami][0].beamInfo.isoCenter.y)[:5]},{str(self.plan.beams[beami][0].beamInfo.isoCenter.z)[:5]}")
			# canvas_textbox = canvas.create_text(10, 40, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text=f"weight: {str(self.plan.beams[beami][segmenti].beamInfo.relativeWeight)}")
			# canvas_textbox = canvas.create_text(10, 55, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text=f"gantryAngle: {str(getattr(self.plan.beams[beami][segmenti].beamInfo.gantryAngle,attr))}")
			# canvas_textbox = canvas.create_text(10, 70, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text=f"collimatorAngle: {str(getattr(self.plan.beams[beami][0].beamInfo.collimatorAngle,attr))}")
			# canvas_textbox = canvas.create_text(10, 85, anchor="nw")
			# canvas.itemconfig(canvas_textbox, text=f"couchAngle: {str(getattr(self.plan.beams[beami][0].beamInfo.couchAngle,attr))}")


		qp.end()




class DosiaMain(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Dosia")
		self.resize(800, 800)
		self.move(300, 300)

		self.topleft = PlanView()
		self.topright = QWidget()
		self.bottomleft = QWidget()
		self.bottomright = QWidget()

		mainLayout = QGridLayout()
		mainLayout.addWidget(self.topleft, 0, 0)
		mainLayout.addWidget(self.topright, 0, 1)
		mainLayout.addWidget(self.bottomleft, 1, 0)
		mainLayout.addWidget(self.bottomright, 1, 1)

		# make all panels take up same space (quadrants)
		mainLayout.setRowStretch(1, 1)
		mainLayout.setRowStretch(2, 1)
		mainLayout.setColumnStretch(0, 1)
		mainLayout.setColumnStretch(1, 1)
		self.setLayout(mainLayout)

if __name__ == '__main__':

	import sys

	app = QApplication(sys.argv)
	Main = DosiaMain()
	Main.show()
	sys.exit(app.exec_())