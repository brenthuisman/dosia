#!/usr/bin/python3

import medimage as image, dicom, gpumcd, numpy as np
from os import path
from gui import *
from PyQt5.QtGui import QIcon

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

		# wid = QWidget(self) #voor als dit een QMainWindow is
		# self.setCentralWidget(wid)
		# wid.setLayout(l)

		self.setLayout(l)



class DosiaMain(QMainWindow):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.setWindowTitle("Dosia")
		self.resize(800, 800)
		self.move(300, 300)
		self.setWindowIcon(QIcon('data/icon.svg'))

		self.sett = gpumcd.Settings()

		# Menu bar
		menu_load_file = QAction('&File(s) (RTPlan, Dose, CT)', self)
		menu_load_file.triggered.connect(self.loadfiles)
		menu_load_dir = QAction('&Directory (CT)', self)
		menu_load_dir.triggered.connect(self.loaddir)
		# menu_open_linaclog = QAction('&Linac Log', self)
		# menu_open_linaclog.triggered.connect(self.loadlinaclog)
		# menu_open_linaclog.setDisabled(True) #TODO: enable if rtplan loaded

		# self.menu_gpumcd_setmachfile = QAction('&Set machine file manually', self)
		# self.menu_gpumcd_setmachfile.triggered.connect(self.setmachfilegpumcd)
		# self.menu_gpumcd_setmachfile.setDisabled(True)
		# self.menu_gpumcd_advanced = QAction('&Advanced', self)
		# self.menu_gpumcd_advanced.triggered.connect(self.settingswindow)
		self.menu_gpumcd_calculate = QAction('&Calculate Dose', self)
		self.menu_gpumcd_calculate.triggered.connect(self.calcgpumcd)
		self.menu_gpumcd_calculate.setDisabled(True)

		menu_bar = self.menuBar()
		menu_open = menu_bar.addMenu('&Load')
		menu_open.addAction(menu_load_file)
		menu_open.addAction(menu_load_dir)

		menu_gpumcd = menu_bar.addMenu('&GPUMCD')
		# menu_gpumcd.addAction(self.menu_gpumcd_setmachfile)
		menu_gpumcd.addAction(self.menu_gpumcd_calculate)
		# menu_gpumcd.addAction(self.menu_gpumcd_advanced)

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
		try:
			if self.planpane.ready and self.ctpane.ready: #no plandoseready
				self.menu_gpumcd_calculate.setDisabled(False)
				# self.menu_gpumcd_setmachfile.setDisabled(False)
		except:
			pass #first launch
		self.setCentralWidget(FourPanel(self.planpane,self.plandosepane,self.ctpane,self.gpumcdpane))

	def settingswindow(self):
		self.setwin = SettingsWindow(self)
		self.setwin.show()

	#TODO: error handling in loading files

	def loadfiles(self):
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
		# fname = str(QFileDialog.getOpenFileName(self, 'Open Dicom Dose')[0])
		# self.topleft = QWidget()#somewidget(fname)
		self.resetpanes()

	def setmachfilegpumcd(self):
		machfile=str(QFileDialog.getOpenFileName(self, 'Load Monaco/GPUMCD machine file')[0])
		self.planpane.plan.accelerator.setmachfile(machfile)

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

	#### TEST PLAN VIEWER
	# fname="D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/1. UPI263538/2.25.1025001435024675917588954042793107482"
	# fname="D:/postdoc/analyses/correcteddicom/F180220C/1.3.46.670589.13.586672257.20190716134201.81016_0001_000000_156328075700a1.dcm"
	# fname="D:/postdoc/analyses/correcteddicom/MonacoPhantom/2.16.840.1.113669.2.931128.223131424.20180410170709.445490_0001_000000_1533630935003e.dcm"
	# p=PlanPane(fname)
	# p.show()

	#### TEST IMAGE VIEWER
	# fname = "D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/2. HalsSupracl + C   3.0  B40s PLAN"
	# fname = "D:/postdoc/analyses/gpumcd_python/dicom/20181101 CTRT KNO-hals/1. UPI263538/2.25.117736802457958133832899838499337503296"
	# p=ImagePane(fname)
	# p.show()


	#### TEST MAIN
	Main = DosiaMain()

	sys.exit(app.exec())