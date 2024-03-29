import numpy as np
import cv2
from pylab import *
from os.path import join, isfile
import sys,os,glob
from ctypes import *
import math
import random

gmm_save_dir='gmm_file_for_video' # saving directory
rgb_save_dir='rgb_frame_for_video'
vid_name='test_vid.flv'
temp_dir='temp_dir'
dim = (640, 640) 
kernel1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)) # opening kernel
kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)) # closing kernel
bkg_ratio=0.7 # sensitivity of the model, lower the value , more sensitive the model
no_of_gmm=20

if not os.path.exists(rgb_save_dir):
    os.makedirs(rgb_save_dir)
print('video is {} is in progress'.format(vid_name))
if not os.path.exists(join(gmm_save_dir)):
    os.makedirs(join(gmm_save_dir))  
fgbg = cv2.createBackgroundSubtractorMOG2(varThreshold=127,detectShadows=False) # shadow false to avoid large fish contour
fgbg.setBackgroundRatio(bkg_ratio) # set the minimum background ratio
fgbg.setNMixtures(no_of_gmm) # setting Gaussian distributions
cap = cv2.VideoCapture(vid_name)
ret, frame = cap.read()
frame=cv2.resize(frame,dim,interpolation = cv2.INTER_AREA)
[img_h,img_w,ch]=shape(frame)
counter=0
while(ret):
   frame=cv2.resize(frame,dim,interpolation = cv2.INTER_AREA)
   obj_arr=[]
   blobs=[]
   fgmask = fgbg.apply(frame,) # default settings where learning rate is automaticalyl selected
   fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel1)
   fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel2)
   img_file="%03d.png" % counter
   cv2.imwrite(join(rgb_save_dir,img_file),frame) 
   cv2.imwrite(join(gmm_save_dir,img_file),fgmask)
   ret, frame = cap.read()
    
   counter+=1
   k = cv2.waitKey(30) & 0xff
   if k == 27:
       break
cap.release()


cv2.destroyAllWindows()