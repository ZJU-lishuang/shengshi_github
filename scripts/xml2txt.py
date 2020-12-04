#coding:utf-8
from __future__ import print_function

import os
import random
import glob
import xml.etree.ElementTree as ET
import shutil
import numpy as np
import cv2

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



def voc2yolo(filename,wh_thr,ar_thr):
    classes_dict = {}
    with open("/home/lishuang/Disk/shengshi_data/new_anti_tail/5classes.names") as f:
        for idx, line in enumerate(f.readlines()):
            class_name = line.strip()
            classes_dict[class_name] = idx
    
    width, height, objects = xml_reader(filename)

    lines = []
    nplines=[]
    for obj in objects:
        x, y, x2, y2 = obj['bbox']
        class_name = obj['name']
        if class_name not in classes_dict:
            continue
        label = classes_dict[class_name]
        #过滤帽子标签
        if label == 3:
            continue
        #其它类别归为一类
        if label > 1:
            label=2
        else:
            minwh=min(x2-x,y2-y)
            wh_thr =min(minwh,wh_thr)
            print("wh_thr=",wh_thr)
            ar_size=(x2-x)*(y2-y)
            ar_size=max(((x2-x)/(y2-y)),((y2-y)/(x2-x)))
            ar_thr=max(ar_thr,ar_size)
            print("ar_thr=",ar_thr)
        cx = (x2+x)*0.5 / width
        cy = (y2+y)*0.5 / height
        w = (x2-x)*1. / width
        h = (y2-y)*1. / height
        line = "%s %.6f %.6f %.6f %.6f\n" % (label, cx, cy, w, h)
        lines.append(line)
        nplines.append([label, cx, cy, w, h])

    # if len(lines)>0 and (np.array(nplines)[:,1:]<=1).all():
    #     txt_name = filename.replace(".xml", ".txt").replace("Annotations/", "txt/")
    #     check_dir(os.path.dirname(txt_name))
    #     with open(txt_name, "w") as f:
    #         f.writelines(lines)

    #     imagepath = os.path.join(os.path.dirname(filename), os.path.basename(filename)[:-(4)] + '.jpg').replace("Annotations/", "JPEGImages/")
    #     save_roiimage_path=imagepath.replace("JPEGImages/", "txt_image/")
    #     check_dir(os.path.dirname(save_roiimage_path))

    #     # img = cv2.imread(imagepath)  # BGR
    #     # img = cv2.resize(img, (int(512), int(256)), interpolation=cv2.INTER_LINEAR)
    #     # cv2.imwrite(save_roiimage_path, img)

    #     shutil.copy(imagepath, save_roiimage_path)
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


def imglist2file(imglist):
    # random.shuffle(imglist)
    # train_list = imglist[:-100]
    # valid_list = imglist[-100:]
    imglist.sort()
    train_list = imglist
    with open("/home/lishuang/Disk/shengshi_data/Xray/xianchang/images/traintxt/2020060502.txt", "w") as f:
        f.writelines(train_list)



if __name__ == "__main__":
    xml_path_list = glob.glob("/home/lishuang/Disk/shengshi_data/new_anti_tail/Annotations/*.xml")
    wh_thr=416
    ar_thr=1
    num=0
    for xml_path in xml_path_list:
        num=num+1
        print("num=",num)
        wh_thr,ar_thr=voc2yolo(xml_path,wh_thr,ar_thr)


    # imglist = get_image_list("/home/lishuang/Disk/shengshi_data/Xray/xianchang/images/train/2020060201")
    # imglist2file(imglist)