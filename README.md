Pythonlibs for Particle/Photon Therapy Analysis
===============================================

This package includes a number of libraries (subdirectories) and tools (scripts in the main dir) created to perform my work as a postdoc, hence `postdoc_tools`. It's a continuation of my `phd_tools` repo, but updated for Python 3 and cruft removed, and new stuff added.

While the scripts are probably of no interest to anyone, some of the libraries may be, which are briefly explained below.

File organisation
-----------------

Files in the root are executable scripts, subdirectories are libraries and could be copied into your own projects or your `$PYTHONPATH`.

Why is this project not neatly separated and split over multiple task-specific repos? Because I am lazy, that's why. And also because just one `rsync` command is required to update all my tools on the clusters I use.

Usage
-----
Clone, and put the directory in your path (`export <CLONE_DIR>:$PATH`). You can get access to the libraries in any script by adding `export PYTHONPATH=<CLONE_DIR>:$PYTHONPATH` to your bashrc, or by putting this atop your scripts:

	import sys
	sys.path.append("<CLONE_DIR>")

 Alternatively, you can cherry-pick. You want to use the `image` library? Just copy the `image` subdir to your project and you're in business.

Now, an incomplete list over the modules with a brief description:

Image
-----

This library supports r/w MetoImage (MHD,ITK) and r/w AVSField (.xdr) images, including NKI compressed images (read-only, useful to work with your Elekta images). The `image` class is a thin wrapper around typed numpy array objects (the `imdata` member) such that you can easily work with images in these data formats. Slicing, projections, mathematical operations, stuff like that is very easy with numpy, so you can easily extend things to what you need.

Of particular interest are the DVH analysis function, and the distance to agreement calculation (entirely based on [npgamma](https://github.com/SimonBiggs/npgamma)). The latter is quite slow though. For [NKI decompression](https://gitlab.com/plastimatch/plastimatch/tree/master/libs/nkidecompress) I supply a 64bit Linux and Windows lib, if you need support for other platforms you can compile the function in `image/nki_decomp` yourself.

Plot
----

A set of function that ease life with Matplotlib. The optional Texify-function make them look good TeX-y, and the tle.py functions provides many ways to compare data (depends on image). I've mostly switched to Seaborn however, which does some of these things already.

Geo
---

Some (spatial) vector functions. In particular, a function to convert Euler angles to matrix angles.

Mac
---

Operate on Gate macro files. Also with extremely basic support for the conversion of a phantom macro to an Image, which you may save to .mhx or .xdr. Requires CLITK tools

RTPlan
---

Some tools for processing dumped RTplans for Gate.

NKI
---

Some custom tools for my postdoc work. Unlikely to be interesting to you.

GPUMCD
------

Work in progress. An interface to the GPUMCD wrapper dll which wraps, you guessed it, GPUMCD.
