import ctypes

def strlist2charpp(stringlist):
	argc = len(stringlist)
	Args = ctypes.c_char_p * (len(stringlist)+1)
	argv = Args(*[ctypes.c_char_p(arg.encode("utf-8")) for arg in stringlist])
	# print(type(argv))
	return argc,argv

def str2charp(string):
	return ctypes.c_char_p(string.encode("utf-8"))

def make_c_array(obj_of_type,N):
	#todo: init each member or not
	return (obj_of_type * N)()

def c_array_to_pointer(array, return_tuple=False):
	if return_tuple == True:
		return len(array), ctypes.cast(array,ctypes.POINTER(type(array[0])))
	else:
		return ctypes.cast(array,ctypes.POINTER(type(array[0])))
