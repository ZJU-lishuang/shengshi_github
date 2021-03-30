#coding:utf-8

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
    obj_struct = {}
    for img in tree.findall('image'):

        obj_attri={}
        obj_attri['height']=img.attrib['height']
        obj_attri['width'] = img.attrib['width']
        obj_all = []
        for obj in img.findall('box'):
            single_obj={}
            single_obj['label'] = obj.attrib['label']
            single_obj['bbox'] = [round(float(obj.attrib['xtl'])),
                                  round(float(obj.attrib['ytl'])),
                                  round(float(obj.attrib['xbr'])),
                                  round(float(obj.attrib['ybr']))]
            for attri in obj.findall('attribute'):
                attri_name=attri.attrib['name']
                single_obj[attri_name]=attri.text

            obj_all.append(single_obj)
        obj_attri['box']=obj_all
        obj_struct[img.attrib['name']]=obj_attri
    return obj_struct

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def cvat2txt(class_name_path,imgdir,txtdir,img_name,value):
    classes_dict = {}
    with open(class_name_path) as f:
        for idx, line in enumerate(f.readlines()):
            class_name = line.strip()
            classes_dict[class_name] = idx

    bndboxs=value['box']
    width=int(value['width'])
    height=int(value['height'])
    filename=os.path.join(imgdir,img_name)

    lines = []
    nplines = []
    ignore_box = True
    if ignore_box:
        imagepath = filename
        if os.path.exists(imagepath):
            img = cv2.imread(imagepath)  # BGR
        else:
            ignore_box=False

    for obj in bndboxs:
        x, y, x2, y2 = obj['bbox']
        class_name = obj['label']
        class_name=class_name.replace("载人", "") #merge two labels

        if class_name not in classes_dict:
            print(f"{obj['label']} is not in classes_dict")
            continue
        
        if '忽略' in obj and obj['忽略'] == "true":
            print(f"this label {obj['label']} is ignore")
            # 填充灰度图覆盖 忽略区域
            if ignore_box:
                mask_pts = np.array([[x, y], [x2, y], [x2, y2], [x, y2]])
                cv2.fillPoly(img, [mask_pts], (114, 114, 114))
            continue

        label = classes_dict[class_name]

        cx = (x2 + x) * 0.5 / width
        cy = (y2 + y) * 0.5 / height
        w = (x2 - x) * 1. / width
        h = (y2 - y) * 1. / height
        line = "%s %.6f %.6f %.6f %.6f\n" % (label, cx, cy, w, h)
        lines.append(line)
        nplines.append([label, cx, cy, w, h])

    if len(lines) > 0 and (np.array(nplines)[:, 1:] <= 1).all():
        txtbasename=os.path.splitext(os.path.basename(img_name))[0]+".txt"
        txt_name=os.path.join(txtdir,txtbasename)
        check_dir(os.path.dirname(txt_name))
        with open(txt_name, "w") as f:
            f.writelines(lines)
        if ignore_box:
            img_save_name=os.path.splitext(os.path.basename(img_name))[0]+".jpg"
            save_roiimage_path = os.path.join(imgdir,img_save_name).replace("imageset/", "txt_image/")
            check_dir(os.path.dirname(save_roiimage_path))
            cv2.imwrite(save_roiimage_path, img)
            # im.save(save_roiimage_path,"jpeg")

if __name__ == "__main__":
    cvatxml="sample/jiaotong/annotations.xml"
    imgdir="sample/jiaotong/imageset"
    txtdir="sample/jiaotong/txt"
    class_name_path="sample/jiaotong/classes.names"
    objects=xml_reader(cvatxml)
    total_num=len(objects)
    i=0
    for obj,value in objects.items():
        i=i+1
        print(f"[{i}/{total_num}]")
        cvat2txt(class_name_path,imgdir,txtdir,obj,value)
