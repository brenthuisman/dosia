#!/usr/bin/python3

import medimage as image, dicom, gpumcd, numpy as np
from gui import *
from PyQt5.QtGui import QIcon

# todo: load this from an ini? gui setting?
sett = gpumcd.Settings("d:\\postdoc\\gpumcd_data")

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
		menu_load_file = QAction('&File(s) (RTPlan, Dose, CT)', self)
		menu_load_file.triggered.connect(self.loadfiles)
		menu_load_dir = QAction('&Directory (CT)', self)
		menu_load_dir.triggered.connect(self.loaddir)
		# menu_open_linaclog = QAction('&Linac Log', self)
		# menu_open_linaclog.triggered.connect(self.loadlinaclog)
		# menu_open_linaclog.setDisabled(True) #TODO: enable if rtplan loaded

		self.menu_gpumcd_calculate = QAction('&Calculate Dose', self)
		self.menu_gpumcd_calculate.triggered.connect(self.calcgpumcd)
		self.menu_gpumcd_calculate.setDisabled(True) #TODO: enable if rtplan and ct loaded
		self.menu_gpumcd_save = QAction('&Save Dose', self)
		self.menu_gpumcd_save.triggered.connect(self.savegpumcd)
		self.menu_gpumcd_save.setDisabled(True) #TODO: enable if gpumcd dose calculated.

		menu_bar = self.menuBar()
		menu_open = menu_bar.addMenu('&Load')
		menu_open.addAction(menu_load_file)
		menu_open.addAction(menu_load_dir)

		menu_gpumcd = menu_bar.addMenu('&GPUMCD')
		menu_gpumcd.addAction(self.menu_gpumcd_calculate)
		menu_gpumcd.addAction(self.menu_gpumcd_save)

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
			if self.planpane.ready and self.plandosepane.ready and self.ctpane.ready:
				self.menu_gpumcd_calculate.setDisabled(False)
		except:
			pass #first launch
		self.setCentralWidget(FourPanel(self.planpane,self.plandosepane,self.ctpane,self.gpumcdpane))

	#TODO: error handling in loading files

	def loadfiles(self):
		files=QFileDialog.getOpenFileNames(self, 'Load Dicom file(s) (RTPlan, Dose, CT)')[0]
		# try:
		for fname in files:
			opendicomobject = dicom.pydicom_object(fname)
			if opendicomobject.modality == "RTPLAN":
				self.planpane = PlanPane(fname,sett)
			if opendicomobject.modality == "CT":
				self.ctpane = ImagePane(fname)
			if opendicomobject.modality == "RTDOSE":
				self.plandosepane = ImagePane(fname)
		# except Exception as e:
		# 	self.popup(f"That was not a valid DICOM file.\n{str(e)}")
		# 	return
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
		dosia = gpumcd.Dosia(sett,self.ctpane.image,self.planpane.plan,self.plandosepane.image)

		self.gpumcdpane = ImagePane(dosia.gpumcd_dose)
		self.menu_gpumcd_save.setDisabled(False)
		self.resetpanes()

	def savegpumcd(self):
		fname = str(QFileDialog.getSaveFileName(self, 'Save GPUMCD Dose')[0])
		self.gpumcdpane.image.saveas(fname)
		# self.topleft = QWidget()#somewidget(fname)
		# self.setCentralWidget(FourPanel(self.topleft,self.topright,self.bottomleft,self.bottomright))

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