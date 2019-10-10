#!/usr/bin/env python

import sys, random

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
	def __init__(self, parent = None, width = 1, height = 1):
		figure = Figure(figsize = (width, height))
		self.axes = figure.add_subplot(111)
		# We want the axes cleared every time plot() is called
		# self.axes.hold(False)

		FigureCanvas.__init__(self, figure)
		# self.setParent(parent)

		FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		num_ints = 10
		random_ints = [ random.randint(0, 10) for i in range(num_ints) ]
		self.axes.clear()
		self.axes.plot(range(num_ints), random_ints, 'r')
		self.draw()

class MainWindow(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose) # Garbage-collect the window after it's been closed.
		self.setWindowTitle("Test window")

		main_widget = QWidget(self)
		self.setCentralWidget(main_widget)

		box_layout = QVBoxLayout(main_widget)

		canvas = MplCanvas(main_widget)
		box_layout.addWidget(canvas)

		self.show()

app = QApplication(sys.argv)
app_window = MainWindow()
sys.exit(app.exec_())