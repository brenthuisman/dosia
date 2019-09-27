#!/usr/bin/env python3
import medimage as image,argparse
from os import path

parser = argparse.ArgumentParser(description='specify mulitple mhd images to analyse')
parser.add_argument('in')
parser.add_argument('out')
opt = parser.parse_args()

print('Converting',path.abspath(opt.in))

im = image.image(path.abspath(opt.in))
if opt.in.endswith('.mhd'):
    im.saveas(path.abspath(opt.in)+'.xdr')
elif opt.in.endswith('.xdr'):
    im.saveas(path.abspath(opt.in)+'.mhd')
else:
    print('No valid input image specified. Aborting...')