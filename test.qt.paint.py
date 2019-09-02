#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial

In this example we draw 6 lines using
different pen styles.

Author: Jan Bodnar
Website: zetcode.com
Last edited: August 2017
"""

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt
import sys

class Example(QWidget):

	def __init__(self):
		super().__init__()

		self.initUI()


	def initUI(self):

		self.setGeometry(300, 300, 280, 270)
		self.setWindowTitle('Pen styles')
		self.show()


	def paintEvent(self, e):

		qp = QPainter()
		qp.begin(self)
		self.drawLines(qp)
		qp.end()


	def resizeEvent(self, e):

		qp = QPainter()
		qp.begin(self)
		self.drawLines(qp)
		qp.end()


	def drawLines(self, qp):
		wf=self.width()/300
		hf=self.height()/300

		pen = QPen(Qt.black, 2, Qt.SolidLine)

		qp.setPen(pen)
		qp.drawLine(20*wf, 40*hf, 250*wf, 40*hf)

		pen.setStyle(Qt.DashLine)
		qp.setPen(pen)
		qp.drawLine(20*wf, 80*hf, 250*wf, 80*hf)

		pen.setStyle(Qt.DashDotLine)
		qp.setPen(pen)
		qp.drawLine(20*wf, 120*hf, 250*wf, 120*hf)

		pen.setStyle(Qt.DotLine)
		qp.setPen(pen)
		qp.drawLine(20*wf, 160*hf, 250*wf, 160*hf)

		pen.setStyle(Qt.DashDotDotLine)
		qp.setPen(pen)
		qp.drawLine(20*wf, 200*hf, 250*wf, 200*hf)

		pen.setStyle(Qt.CustomDashLine)
		pen.setDashPattern([1, 4, 5, 4])
		qp.setPen(pen)
		qp.drawLine(20*wf, 240*hf, 250*wf, 240*hf)


if __name__ == '__main__':

	app = QApplication(sys.argv)
	ex = Example()
	sys.exit(app.exec_())