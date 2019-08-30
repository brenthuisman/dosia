#!/usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class BSlider(QWidget):
	def __init__(self, title, minval,maxval,defval,orientation=Qt.Horizontal, parent=None):
		super().__init__(parent)

		self.value = defval

		self.slider = QSlider(orientation,self)
		self.slider.setMinimum(minval)
		self.slider.setMaximum(maxval)
		self.slider.setValue(defval)
		self.slider.valueChanged[int].connect(self.changeValue)

		self.title = QLabel(title,self)

		self.vallabel = QLabel(str(defval),self)
		self.vallabel.setAlignment(Qt.AlignCenter)

		l = QVBoxLayout()
		l.addWidget(self.title)
		l.addWidget(self.slider)
		l.addWidget(self.vallabel)
		self.setLayout(l)

	def changeValue(self,v):
		self.value = v
		self.vallabel.setText(str(v))


class PlanView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent) #init superclass. Do we need to pass parent?

		self.beam_slider = BSlider("Beam index",0,2,1)
		self.segment_slider = BSlider("Segment index",0,20,1)
		self.startend_slider = BSlider("Start <> Stop",0,1,0)


		planLayout = QHBoxLayout()
		# TODO figure out why strechtfactor has no effect
		planLayout.addWidget(self.beam_slider,0.3)
		planLayout.addWidget(self.segment_slider,0.7)
		planLayout.addWidget(self.startend_slider,0)

		#TODO add drawpane

		self.setLayout(planLayout)




class DosiaMain(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent) #init superclass. Do we need to pass parent?
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