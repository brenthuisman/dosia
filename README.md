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

`dll` contains some dlls required to run GPUMCD, including the wrapper dll that I provide to you without source code, because at this time I am not 100% sure I can license it the same as this repo. All files here are provided as a courtesy and are excluded from the license of this repo.

Installation
------------

Right now, you must install the dependencies yourself.

    $ pip(3) install medimage pyqt5

This repo does NOT include GPUMCD, as this is not freely available software. You need to obtain GPUMCD from Elekta, in the form of a file called `GPUMonteCarloDoseLibrary.dll`, which could be provided to you as part of the Monaco treatment planning software, typically installed to `C:\Program Files\CMS\Monaco`. Right now, this file must be copied and placed in the `dll` subdir of this project.

Usage
-----

A few scripts using the libraries are provided in the root of this repo. The most sophisticated one is gui.py. This allows you to load a ct, plan, dose combo and inspect the images and plan. Right now, you must manually load the machine file as well. If GPUMCD was found, the dose calculation should be available and work!.
