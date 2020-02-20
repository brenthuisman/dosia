Dosia
=====

This package comprises Python bindings for GPUMCD (Hissoiny et al. 2011), dicom parser for CT's, RTDoses, and RTplans, and a dose computation tool based on the GPUMCD bindings. Note that this means this package won't work on platforms other than Windows x64, as GPUMCD does not.

In the design my philosophy is, library first, scripts second, gui third. I am happy to report I can deliver on all fronts at this time :)

File organisation
-----------------

Files in the root are executable scripts, subdirectories are libraries. The `data` folder includes material data from [NIST](https://materialsdata.nist.gov/), CT Hounsfield conversion data and an icon image.

`gpumcd` directory contains the GPUMCD bindings and parsers to convert dicom object data into the structures that can be handled by the dose computation engine. The `Dosia` class in `__init__.py` is what you should be using and should be fairly self-explanatory.

`gui` contains a few `QWidget` derived classes for visualizing `medimage` objects and RTplans. Handy for visually scrolling through the controlpoints of your plan.

`dicom` contains a small helper class to quickly get relevant data from a dicom file, and a function that helps you loop the dose engine over large quantities of treatments.

`example_dosia_ini_dir` is a 'starter' for a 'dosia.ini directory'. This directory requires a dosia.ini file, with which you can configure Dosia. In addition, some other data is required: hounsfield tables, material data, GPUMCD machine files and some dlls including GPUMCD itself. The former two I provide here, as those data are public domain (your institute may use another HU-table of course). The latter two I do not provide, but the directories provide instructions in `placeholder.txt` on how to configure them.

Installation
------------

Right now, you must install the dependencies yourself.

    $ pip3 install medimage pyqt5

`git pull` or download this repo somewhere, and optionally move the `example_dosia_ini_dir` (you could have multiple). Then, populate the `dll` directory in that 'dosia.ini directory'. Put your machinefiles in the machines directory, and make sure dosia.ini points to them (use relative paths).

This repo does NOT include GPUMCD, as this is not freely available software. You need to obtain GPUMCD from Elekta, in the form of a file called `GPUMonteCarloDoseLibrary.dll`, which could be provided to you as part of the Monaco treatment planning software, typically installed to `C:\Program Files\CMS\Monaco`.

Usage
-----

A few scripts using the libraries are provided in the root of this repo. The most sophisticated one is gui.py. This allows you to load a ct, plan, dose combo and inspect the images and plan using a simple viewer. Upon first run of the program, you need to set a 'dosia.ini directory', which will be remembered for further runs, but can always be changes in the menu. If you load a TPS dose, that grid is use for the GPUMCD dose calc. If you do not load a TPS dose, the a 3x3x3mm^3 grid is created with the CT extents and used for the GPUMCD dose calc.
