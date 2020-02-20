#!/usr/bin/python3

import medimage as image, dicom, gpumcd, numpy as np
from os import path
from gui import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings

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


class SettingsWindow(QWidget): #FIXME, waarom QWindow niet gevonden?
	def __init__(self,parent, *args,**kwargs):
		super().__init__(*args,**kwargs)

		l = QVBoxLayout()
		sett = parent.sett

		self.menu_advanced_sumbeams = QCheckBox("Sum dose over beams")
		self.menu_advanced_sumbeams.setChecked(sett.dose['sum_beams'])
		self.menu_advanced_magnetic_field = QSpinBox()
		self.menu_advanced_magnetic_field.setValue(sett.dose['magnetic_field'])
		self.menu_advanced_magnetic_field.setSuffix('T magnetic field')
		self.menu_advanced_field_margin = QSpinBox()
		self.menu_advanced_field_margin.setValue(sett.dose['field_margin'])
		self.menu_advanced_field_margin.setSuffix('mm field margin')
		self.menu_advanced_dose_per_fraction = QCheckBox("Dose per fraction or all fractions")
		self.menu_advanced_dose_per_fraction.setChecked(sett.dose['dose_per_fraction'])

		l.addWidget(self.menu_advanced_sumbeams,1)
		l.addWidget(self.menu_advanced_magnetic_field,1)
		l.addWidget(self.menu_advanced_field_margin,1)
		l.addWidget(self.menu_advanced_dose_per_fraction,1)

		self.setLayout(l)


class DosiaMain(QMainWindow):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.setWindowTitle("Dosia")
		self.resize(800, 800)
		self.move(300, 300)
		self.setWindowIcon(QIcon('gui/icon.svg'))
		self.guisettings = QSettings("BrentH", "Dosia")

		# Must load a valid dosia.ini dir
		if self.guisettings.value("dosiainidir") == None:
			self.setdosiainidir()
		else:
			self.sett = gpumcd.Settings(self.guisettings.value("dosiainidir"))

		# Menu bar
		self.menu_load_file = QAction('&File(s) (RTPlan, Dose, CT)', self)
		self.menu_load_file.triggered.connect(self.loadfiles)
		self.menu_load_dir = QAction('&Directory (CT)', self)
		self.menu_load_dir.triggered.connect(self.loaddir)
		# self.menu_open_linaclog = QAction('&Linac Log', self)
		# self.menu_open_linaclog.triggered.connect(self.loadlinaclog)
		# self.menu_open_linaclog.setDisabled(True) #TODO: enable if rtplan loaded

		self.menu_gpumcd_calculate = QAction('&Calculate Dose with GPUMCD', self)
		self.menu_gpumcd_calculate.triggered.connect(self.calcgpumcd)
		self.menu_gpumcd_calculate.setDisabled(True)

		self.menu_setdosiainidir = QAction('&Set Dosia.ini directory', self)
		self.menu_setdosiainidir.triggered.connect(self.setdosiainidir)

		self.menu_bar = self.menuBar()
		self.menu_open = self.menu_bar.addMenu('&Load')
		self.menu_open.addAction(self.menu_load_file)
		self.menu_open.addAction(self.menu_load_dir)

		self.menu_gpumcd = self.menu_bar.addMenu('&Calculate')
		self.menu_gpumcd.addAction(self.menu_gpumcd_calculate)

		self.menu_dosia = self.menu_bar.addMenu('&Dosia')
		self.menu_dosia.addAction(self.menu_setdosiainidir)

		# Quadrants
		self.planpane = QWidget()
		self.plandosepane = QWidget()
		self.ctpane = QWidget()
		self.gpumcdpane = QWidget()
		self.resetpanes()

		# statusbar
		self.statusBar().showMessage(f'dosia.ini in {self.guisettings.value("dosiainidir")} loaded.')

		# done!
		self.show()

	def resetpanes(self):
		try:
			if self.planpane.ready and self.ctpane.ready: #no plandoseready
				self.menu_gpumcd_calculate.setDisabled(False)
				# self.menu_gpumcd_setmachfile.setDisabled(False)
		except:
			pass #first launch
		self.setCentralWidget(FourPanel(self.planpane,self.plandosepane,self.ctpane,self.gpumcdpane))

	def loadfiles(self):
		# TODO: error handling in loading files
		files=QFileDialog.getOpenFileNames(self, 'Load Dicom file(s) (RTPlan, Dose, CT)')[0]
		# try:
		for fname in files:
			opendicomobject = dicom.pydicom_object(fname)
			if opendicomobject.modality == "RTPLAN":
				self.planpane = PlanPane(fname,self.sett)
			if opendicomobject.modality == "CT":
				self.ctpane = ImagePane(fname,self.sett)
			if opendicomobject.modality == "RTDOSE":
				self.plandosepane = ImagePane(fname,self.sett)
		# except Exception as e:
		# 	self.popup(f"That was not a valid DICOM file.\n{str(e)}")
		# 	return
		self.resetpanes()

	def loaddir(self):
		fname = str(QFileDialog.getExistingDirectory(self, 'Open Dicom CT (slices) directory'))
		try:
			opendicomobject = dicom.pydicom_object(fname)
			assert opendicomobject.modality == "CT", "That directory did not contain a valid set of DICOM CT slices."
			self.ctpane = ImagePane(fname,self.sett)
		except Exception as e:
			self.popup(f"That was not a valid DICOM file.\n{str(e)}")
			return
		self.resetpanes()

	def loadcase(self):
		# TODO: open dir and search for rtplan,ct,dose and set panes accordingly.
		# multiple rtplan selector?
		pass

	def loadlinaclog(self):
		# TODO
		# fname = str(QFileDialog.getOpenFileName(self, 'Open Dicom Dose')[0])
		# self.topleft = QWidget()#somewidget(fname)
		self.resetpanes()

	def setdosiainidir(self):
		dosiainidir = str(QFileDialog.getExistingDirectory(self, 'Set Dosia.ini directory directory'))
		self.guisettings.setValue("dosiainidir", dosiainidir)

	def calcgpumcd(self):
		try:
			self.plandosepane.ready
			dosia = gpumcd.Dosia(self.sett,self.ctpane.image[0],self.planpane.plan,self.plandosepane.image[0])
		except:
			c = self.ctpane.image[0].copy()
			c.resample([3,3,3])
			c.zero_out()
			dosia = gpumcd.Dosia(self.sett,self.ctpane.image[0],self.planpane.plan,c)
		self.gpumcdpane = ImagePane(dosia.gpumcd_dose,self.sett)
		if self.sett.dose['output_cgy']:
			for img in self.gpumcdpane.image:
				img.mul(100)
		self.resetpanes()

	def popup(self,message):
		a = QMessageBox()
		a.setText(message)
		a.exec()
		print(str(message))


if __name__ == '__main__':
	import sys

	app = QApplication(sys.argv)
	Main = DosiaMain()
	sys.exit(app.exec())