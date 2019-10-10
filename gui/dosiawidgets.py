import medimage as image,gpumcd,dicom,numpy as np
from .widgets import BSlider

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPainter, QPen, QImage, QPixmap
from PyQt5.QtCore import Qt,QSize

class ImagePane(QWidget):
	def __init__(self, fname, *args,**kwargs):
		super().__init__(*args,**kwargs)

		if isinstance(fname,image.image):
			self.image = fname.copy()
		else:
			self.image = image.image(fname)

		x,y,z=self.image.get_slices_at_index()
		# import scipy.misc
		# scipy.misc.imsave("d:/slicex.png",x)
		# scipy.misc.imsave("d:/slicey.png",y)
		# scipy.misc.imsave("d:/slicez.png",z)
		s=np.uint8(np.interp(x, (x.min(), x.max()), (0, 255)).T)
		im = np.copy(np.rot90(np.rot90(s)),order='C')
		self.qimage = QImage(im.data,im.shape[1],im.shape[0],im.shape[1]*1,QImage.Format_Grayscale8)

		self.ready = True

	def paintEvent(self,e):
		painter = QPainter(self)
		painter.drawPixmap(self.rect(), QPixmap(self.qimage))

	def minimumSizeHint(self):
		return QSize(200, 200)


class PlanPane(QWidget):
	def __init__(self, fname, sett, *args,**kwargs):
		super().__init__(*args,**kwargs)

		opendicomobject = dicom.pydicom_object(fname)
		self.plan = gpumcd.Rtplan(sett,opendicomobject)

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
		self.ready = True

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
		pen = QPen(Qt.black, 1, Qt.SolidLine)

		h400 = h/2 # TEST
		w400 = w/2 # TEST
		vert_zoom= w400 / 400. * 20
		hor_zoom= h400 / 400. * 20
		leafedges = np.linspace(0,h,plan.accelerator.leafs_per_bank+1)

		if segment.collimator.mlc.orientation.value == -1:
			pen.setStyle(Qt.DashLine)
		else:
			pen.setStyle(Qt.SolidLine)
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

		#jaws
		if segment.collimator.parallelJaw.orientation.value == -1:
			pen.setStyle(Qt.DashLine)
		else:
			pen.setStyle(Qt.SolidLine)
		# if segment.collimator.parallelJaw.orientation.value is not -1:
		l,r = vert_zoom* getattr(segment.collimator.parallelJaw.j1,attr), vert_zoom * getattr(segment.collimator.parallelJaw.j2,attr)
		pen.setColor(Qt.green)
		pen.setWidth(2)
		qp.setPen(pen)
		qp.drawLine(w400+l, 0, w400+l, h)
		pen.setColor(Qt.blue)
		qp.setPen(pen)
		qp.drawLine(w400+r, 0, w400+r, h)


		if segment.collimator.perpendicularJaw.orientation.value == -1:
			pen.setStyle(Qt.DashLine)
		else:
			pen.setStyle(Qt.SolidLine)
		# if segment.collimator.perpendicularJaw.orientation.value is not -1:
		t,b = hor_zoom* getattr(segment.collimator.perpendicularJaw.j1,attr), hor_zoom * getattr(segment.collimator.perpendicularJaw.j2,attr)
		pen.setColor(Qt.cyan)
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

		pen.setColor(Qt.black)
		qp.setPen(pen)
		qp.drawText(10, 10,"viewport: 40cm x 40cm")
		qp.drawText(10, 25, f"isoCenter: {str(self.plan.beams[self.bi][0].beamInfo.isoCenter.x)[:5]},{str(self.plan.beams[self.bi][0].beamInfo.isoCenter.y)[:5]},{str(self.plan.beams[self.bi][0].beamInfo.isoCenter.z)[:5]}")
		qp.drawText(10, 40, f"weight: {str(segment.beamInfo.relativeWeight)}")
		qp.drawText(10, 55, f"gantryAngle: {str(getattr(segment.beamInfo.gantryAngle,attr))}")
		qp.drawText(10, 70, f"collimatorAngle: {str(getattr(self.plan.beams[self.bi][0].beamInfo.collimatorAngle,attr))}")
		qp.drawText(10, 85, f"couchAngle: {str(getattr(self.plan.beams[self.bi][0].beamInfo.couchAngle,attr))}")

		qp.end()
