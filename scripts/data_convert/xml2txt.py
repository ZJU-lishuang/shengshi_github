#coding:utf-8
from __future__ import print_function

import os
import random
import glob
import xml.etree.ElementTree as ET
import shutil
import numpy as np
import cv2
import math

def xml_reader(filename):
    """ Parse a PASCAL VOC xml file """
    tree = ET.parse(filename)
    print(filename)
    size = tree.find('size')
    width = int(size.find('width').text)
    height = int(size.find('height').text)
    objects = []
    for obj in tree.findall('object'):
        obj_struct = {}
        obj_struct['name'] = obj.find('name').text
        bbox = obj.find('bndbox')
        obj_struct['bbox'] = [round(float(bbox.find('xmin').text)),
                              round(float(bbox.find('ymin').text)),
                              round(float(bbox.find('xmax').text)),
                              round(float(bbox.find('ymax').text))]
        objects.append(obj_struct)
    return width, height, objects

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)



def voc2yolo(filename,class_name_path,wh_thr,ar_thr):
    classes_dict = {}
    with open(class_name_path) as f:
        for idx, line in enumerate(f.readlines()):
            class_name = line.strip()
            classes_dict[class_name] = idx
    
    
    width, height, objects = xml_reader(filename)
    label_folder="Annotations/"
    image_folder="JPEGImages/"
    txt_folder="txt/"
    newimage_folder="txt_image/"

    lines = []
    nplines=[]
    ignore_box=True
    if ignore_box:
        imagepath = os.path.join(os.path.dirname(filename), os.path.splitext(os.path.basename(filename))[0] + '.jpg').replace(label_folder, image_folder)
        img = cv2.imread(imagepath)  # BGR

    for obj in objects:
        x, y, x2, y2 = obj['bbox']
        class_name = obj['name']
        if class_name not in classes_dict:
            print(f"{class_name} is not in classes_dict")
            #填充灰度图覆盖 忽略区域
            if ignore_box:
                mask_pts=np.array([[x,y],[x2,y],[x2,y2],[x,y2]])
                cv2.fillPoly(img, [mask_pts], (114,114,114))
            continue
        label = classes_dict[class_name]

        cx = (x2+x)*0.5 / width
        cy = (y2+y)*0.5 / height
        w = (x2-x)*1. / width
        h = (y2-y)*1. / height
        line = "%s %.6f %.6f %.6f %.6f\n" % (label, cx, cy, w, h)
        lines.append(line)
        nplines.append([label, cx, cy, w, h])

    if len(lines)>0 and (np.array(nplines)[:,1:]<=1).all():
        txt_name = filename.replace(".xml", ".txt").replace(label_folder, txt_folder)
        check_dir(os.path.dirname(txt_name))
        with open(txt_name, "w") as f:
            f.writelines(lines)
    if ignore_box:
        save_roiimage_path=imagepath.replace(image_folder, newimage_folder)
        check_dir(os.path.dirname(save_roiimage_path))
        cv2.imwrite(save_roiimage_path, img)
    return wh_thr,ar_thr

def get_image_list(image_dir, suffix=['jpg', 'jpeg', 'JPG', 'JPEG','png']):
    '''get all image path ends with suffix'''
    if not os.path.exists(image_dir):
        print("PATH:%s not exists" % image_dir)
        return []
    imglist = []
    for root, sdirs, files in os.walk(image_dir):
        if not files:
            continue
        for filename in files:
            filepath = os.path.join(root, filename) + "\n"
            if filename.split('.')[-1] in suffix:
                imglist.append(filepath)
    return imglist


def imglist2file(imglist,val_percent=0.1):
    random.shuffle(imglist)
    img_len=len(imglist)
    val_len=math.ceil(img_len*val_percent)*-1
    train_list = imglist[:val_len]
    valid_list = imglist[val_len:]
    # imglist.sort()
    # train_list = imglist
    with open("sample/yolo/train.txt", "w") as f:
        f.writelines(train_list)
    with open("sample/yolo/val.txt", "w") as f:
        f.writelines(valid_list)



if __name__ == "__main__":
    xml_path_list = glob.glob("sample/yolo/Annotations/*.xml")
    class_name_path="sample/yolo/classes.names"
    wh_thr=416
    ar_thr=1
    num=0
    for xml_path in xml_path_list:
        num=num+1
        print("num=",num)
        wh_thr,ar_thr=voc2yolo(xml_path,class_name_path,wh_thr,ar_thr)


    imglist = get_image_list("sample/yolo/JPEGImages")
    imglist2file(imglist)