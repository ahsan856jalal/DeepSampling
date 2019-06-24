import numpy as np
import cv2
from pylab import *
from os.path import join, isfile
import sys,os,glob
from ctypes import *
import math
import random


#gmm_save_dir='/home/ahsanjalal/Fishclef/MEE_application/gmm_files'
temp_dir='/home/ahsanjalal/Fishclef/MEE_application/temp_dir'
optical_save_dir='/home/ahsanjalal/Fishclef/MEE_application/optical_files'
#yolo_save_dir='/home/ahsanjalal/Fishclef/MEE_application/yolo_files'
optical_original='/home/ahsanjalal/Fishclef/MEE_application/optical_original'

def sample(probs):
    s = sum(probs)
    probs = [a/s for a in probs]
    r = random.uniform(0, 1)
    for i in range(len(probs)):
        r = r - probs[i]
        if r <= 0:
            return i
    return len(probs)-1

def c_array(ctype, values):
    arr = (ctype*len(values))()
    arr[:] = values
    return arr

class BOX(Structure):os
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]

class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]

    

#lib = CDLL("/home/pjreddie/documents/darknet/libdarknet.so", RTLD_GLOBAL)
lib = CDLL("/home/ahsanjalal/darknet_pj/libdarknet.so", RTLD_GLOBAL)
lib.network_width.argtypes = [c_void_p]
lib.network_width.restype = c_int
lib.network_height.argtypes = [c_void_p]
lib.network_height.restype = c_int

predict = lib.network_predict
predict.argtypes = [c_void_p, POINTER(c_float)]
predict.restype = POINTER(c_float)

set_gpu = lib.cuda_set_device
set_gpu.argtypes = [c_int]

make_image = lib.make_image
make_image.argtypes = [c_int, c_int, c_int]
make_image.restype = IMAGE

get_network_boxes = lib.get_network_boxes
get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
get_network_boxes.restype = POINTER(DETECTION)

make_network_boxes = lib.make_network_boxes
make_network_boxes.argtypes = [c_void_p]
make_network_boxes.restype = POINTER(DETECTION)

free_detections = lib.free_detections
free_detections.argtypes = [POINTER(DETECTION), c_int]

free_ptrs = lib.free_ptrs
free_ptrs.argtypes = [POINTER(c_void_p), c_int]

network_predict = lib.network_predict
network_predict.argtypes = [c_void_p, POINTER(c_float)]

reset_rnn = lib.reset_rnn
reset_rnn.argtypes = [c_void_p]

load_net = lib.load_network
load_net.argtypes = [c_char_p, c_char_p, c_int]
load_net.restype = c_void_p

do_nms_obj = lib.do_nms_obj
do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

do_nms_sort = lib.do_nms_sort
do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

free_image = lib.free_image
free_image.argtypes = [IMAGE]

letterbox_image = lib.letterbox_image
letterbox_image.argtypes = [IMAGE, c_int, c_int]
letterbox_image.restype = IMAGE

load_meta = lib.get_metadata
lib.get_metadata.argtypes = [c_char_p]
lib.get_metadata.restype = METADATA

load_image = lib.load_image_color
load_image.argtypes = [c_char_p, c_int, c_int]
load_image.restype = IMAGE

rgbgr_image = lib.rgbgr_image
rgbgr_image.argtypes = [IMAGE]

predict_image = lib.network_predict_image
predict_image.argtypes = [c_void_p, IMAGE]
predict_image.restype = POINTER(c_float)

def array_to_image(arr):
    # need to return old values to avoid python freeing memory
    arr = arr.transpose(2,0,1)
    c, h, w = arr.shape[0:3]
    arr = np.ascontiguousarray(arr.flat, dtype=np.float32) / 255.0
    data = arr.ctypes.data_as(POINTER(c_float))
    im = IMAGE(w,h,c,data)
    return
    
def classify(net, meta, im):
    out = predict_image(net, im)
    res = []
    for i in range(meta.classes):
        res.append((meta.names[i], out[i]))
    res = sorted(res, key=lambda x: -x[1])
    return res

def detect(net, meta, image, thresh=.2, hier_thresh=.5, nms=.45):
    """if isinstance(image, bytes):  
        # image is a filename 
        # i.e. image = b'/darknet/data/dog.jpg'
        im = load_image(image, 0, 0)
    else:  
        # image is an nparray
        # i.e. image = cv2.imread('/darknet/data/dog.jpg')
        im, image = array_to_image(image)
        rgbgr_image(im)
    """
    im, image = array_to_image(image)
    rgbgr_image(im)
    num = c_int(0)
    pnum = pointer(num)
    predict_image(net, im)
    dets = get_network_boxes(net, im.w, im.h, thresh, 
                             hier_thresh, None, 0, pnum)
    num = pnum[0]
    if nms: do_nms_obj(dets, num, meta.classes, nms)

    res = []
    for j in range(num):
        a = dets[j].prob[0:meta.classes]
        if any(a):
            ai = np.array(a).nonzero()[0]
            for i in ai:
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], 
                           (b.x, b.y, b.w, b.h)))

    res = sorted(res, key=lambda x: -x[1])
    if isinstance(image, bytes): free_image(im)
    free_detections(dets, num)
    return res
    
specie_list= ["vaigiensis",
             "nigrofuscus",
             "clarkii",
             "lununatus",
             "speculum",    
             "trifascialis",
             "chrysura",
             "aruanus",
             "reticulatus",
             "malapterus",
             "kuntee",
             "nigroris",
             "vanicolensis",
             "dickii",
            "scopas",
            "background"]    
net = load_net(b"/home/ahsanjalal/darknet_pj/cfg/resnet50.cfg", b"/home/ahsanjalal/darknet_pj/resnet_50_16_classes/resnet50_146.weights", 0)
meta = load_meta(b"/home/ahsanjalal/darknet_pj/cfg/fish_classification.data")


########################  Optical classification##########################################

cap = cv2.VideoCapture('9c333821ab0e2a9e4c5209065c415309#201102031130_s3_0.flv')
ret, frame1 = cap.read()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2))
prvs = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[...,1] = 255
fshape = frame1.shape
img_h = fshape[0]
img_w = fshape[1]
img_yuv = cv2.cvtColor(frame1, cv2.COLOR_BGR2YUV)
aa=0
# for first file 
img_file='image_0.png'
f = open(join(optical_save_dir,img_file).split('.png')[0]+'.txt', "w")
f.close()
        
while(1):
    aa+=1
    ret, frame2 = cap.read()
    if(ret==True):
        next = cv2.cvtColor(frame2,cv2.COLOR_BGR2GRAY)
        obj_arr=[]
        blobs=[]
        flow = cv2.calcOpticalFlowFarneback(prvs,next, None, 0.95, 10, 15, 3, 5, 1.2, 0)
    
        mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
        hsv[...,0] = ang*180/np.pi/2
        hsv[...,2] = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX)
        rgb = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
        ret, threshed_img = cv2.threshold(cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY),
                    55, 255, cv2.THRESH_BINARY)
        fgmask = cv2.morphologyEx(threshed_img, cv2.MORPH_OPEN, kernel)
        fgmask = cv2.morphologyEx(threshed_img, cv2.MORPH_CLOSE, kernel)
        img_file='image_{}.png'.format(aa)
        if not os.path.exists(optical_original):
            os.makedirs(optical_original)
        cv2.imwrite(join(optical_original,img_file),fgmask)
        _, contours, _= cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt)>200:
                blobs.append(cnt)
        for blb in blobs:
            (x,y,w,h) = cv2.boundingRect(blb)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            img_patch=frame2[y:y+h,x:x+w]
            img_patch = cv2.resize(img_patch.astype('float32'), dsize=(50,50))
            cv2.imwrite(temp_dir+'/'+ "true_image.png", img_patch)
            im = load_image(temp_dir+'/'+ "true_image.png", 0, 0)
            r = classify(net, meta, im)
            r=r[0]
            fish_label_det=specie_list.index(r[0])
            if(fish_label_det!=15 and r[1]>0.4):
    
                x = (x+w/2.0) / img_w
                y = (y+h/2.0) / img_h
                w = float(w) / img_w
                h = float(h) / img_h
                fish_specie=fish_label_det
                tmp = [fish_specie, x, y, w, h]
                obj_arr.append(tmp)
        xml_content = ""
        for obj in obj_arr:
            xml_content += "%d %f %f %f %f\n" % (obj[0], obj[1], obj[2], obj[3], obj[4])
        if not os.path.exists(optical_save_dir):
            os.makedirs(optical_save_dir)
        
        f = open(join(optical_save_dir,img_file).split('.png')[0]+'.txt', "w")
        f.write(xml_content)
        f.close()
        cv2.imwrite(join(optical_save_dir,img_file),frame2)
        cv2.imshow('threshold',fgmask)
        cv2.imshow('optical_out',rgb)

        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break
        prvs = next
    else:
        break
cap.release()
#out.release()
cv2.destroyAllWindows()
