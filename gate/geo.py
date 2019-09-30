from math import acos,cos,sin,sqrt

def rotator(heading, attitude, bank):
	'''
	Converts from euler angles to matrix angles (or something like that, I'm not even sure.)
	src:
	http://proj-clhep.web.cern.ch/proj-clhep/doc/CLHEP_2_1_3_1/doxygen/html/Rotation_8cc-source.html#l00153
	Gate and Geant4 rotations actually are typedefd CLHEP rotations.
	http://www.euclideanspace.com/maths/geometry/rotations/conversions/eulerToMatrix/index.htm
	'''
	ch = cos(heading)
	sh = sin(heading)
	ca = cos(attitude)
	sa = sin(attitude)
	cb = cos(bank)
	sb = sin(bank)
	m00 = ch * ca
	m01 = sh*sb - ch*sa*cb
	m02 = ch*sa*sb + sh*cb
	m10 = sa
	m11 = ca*cb
	m12 = -ca*sb
	m20 = -sh*ca
	m21 = sh*sa*cb + ch*sb
	m22 = -sh*sa*sb + ch*cb

	cosa  = 0.5*(m00+m11+m22-1)
	cosa1 = 1-cosa
	angle=[]
	aaxis=[]
	if (cosa1 <= 0):
		angle = [0]
		aaxis = [0,0,1]
	else:
		x=0
		y=0
		z=0
		if (m00 > cosa): x = sqrt((m00-cosa)/cosa1)
		if (m11 > cosa): y = sqrt((m11-cosa)/cosa1)
		if (m22 > cosa): z = sqrt((m22-cosa)/cosa1)
		if (m21 < m12): x = -x
		if (m02 < m20): y = -y
		if (m10 < m01): z = -z
		#angle = (cosa < -1.) ? std::acos(-1.) : std::acos(cosa);
		#angle = (cosa < -1.) ? acos(-1.) : acos(cosa)
		if cosa < -1.:
			angle = [acos(-1.)]
		else:
			angle = [acos(cosa)]
		aaxis = [x,y,z]
	angle[0]=degrees(angle[0])
	angle.extend(aaxis)
	return angle

#http://stackoverflow.com/questions/4870393/rotating-coordinate-system-via-a-quaternion
def normalize(v, tolerance=0.00001):
    mag2 = sum(n * n for n in v)
    if abs(mag2 - 1.0) > tolerance:
        mag = sqrt(mag2)
        v = tuple(n / mag for n in v)
    return v

def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return w, x, y, z

def q_conjugate(q):
    w, x, y, z = q
    return (w, -x, -y, -z)

def qv_mult(q1, v1):
    q2 = (0.0,) + v1
    return q_mult(q_mult(q1, q2), q_conjugate(q1))[1:]

def axisangle_to_q(v, theta):
    v = normalize(v)
    x, y, z = v
    theta /= 2
    w = cos(theta)
    x = x * sin(theta)
    y = y * sin(theta)
    z = z * sin(theta)
    return w, x, y, z

def q_to_axisangle(q):
    w, v = q[0], q[1:]
    theta = acos(w) * 2.0
    return normalize(v), theta



# Here's a quick usage example. A sequence of 90-degree rotations about the x, y, and z axes will return a vector on the y axis to its original position. This code performs those rotations:

# x_axis_unit = (1, 0, 0)
# y_axis_unit = (0, 1, 0)
# z_axis_unit = (0, 0, 1)
# r1 = axisangle_to_q(x_axis_unit, numpy.pi / 2)
# r2 = axisangle_to_q(y_axis_unit, numpy.pi / 2)
# r3 = axisangle_to_q(z_axis_unit, numpy.pi / 2)

# v = qv_mult(r1, y_axis_unit)
# v = qv_mult(r2, v)
# v = qv_mult(r3, v)

# print v
