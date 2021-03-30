import os
import numpy as np
import cv2
import json
import xml.etree.ElementTree as ET

def voc_classes():
    return [
        'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat',
        'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person',
        'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'
    ]

def custom_classes():
    return [
        '1'
    ]

label_ids = {name: i for i, name in enumerate(custom_classes())}

def subfiles(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and not entry.is_dir():
            yield entry.name

def loadAllTagFile( DirectoryPath, tag ):# download all files' name
    result = []
    for file in subfiles(DirectoryPath):
    # for file in os.listdir(DirectoryPath):
        file_path = os.path.join(DirectoryPath, file)
        if os.path.splitext(file_path)[1] == tag:
            result.append(file_path)
    return result

output_json="sample/yolo/json"
os.makedirs(output_json, exist_ok=True)  #检查目录
output_jpg="sample/yolo/JPEGImages"
output_xml="sample/yolo/Annotations"

fig_names = loadAllTagFile(output_jpg, '.jpg')
xml_files= loadAllTagFile(output_xml, '.xml')
xml_files.sort()
fig_names.sort()

image_jsons=[]

for fig_name in fig_names:

    img_basename=os.path.basename(fig_name)
    xml_basename=os.path.splitext(img_basename)[0]+".xml"
    xml_path=os.path.join(output_xml,xml_basename)
    json_save_path=os.path.join(output_json,os.path.splitext(img_basename)[0]+".json")
    if xml_path in xml_files:
        ann_dict = {}
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size = root.find('size')
        w = int(size.find('width').text)
        h = int(size.find('height').text)
        ann_dict["filename"]=fig_name
        ann_dict["imageData"] = None
        ann_dict["imgHeight"] = h
        ann_dict["imgWidth"] = w
        ann_dict["version"] = "v1.0"
        ann_dict["flags"] = {}
        ann_dict["shapes"]=[]
        # ann_dict["lineColor"] = null
        # ann_dict["fillColor"] = null
        shape={}
        for obj in root.findall('object'):
            name = obj.find('name').text
            label = label_ids[name]
            bnd_box = obj.find('bndbox')
            bbox = [
                int(bnd_box.find('xmin').text),
                int(bnd_box.find('ymin').text),
                int(bnd_box.find('xmax').text),
                int(bnd_box.find('ymax').text)
            ]
            shape['label']=name
            # shape["lineColor"] = null
            # shape["fillColor"] = null
            shape['points']=[bbox[:2],bbox[2:]]
            shape['shape_type']="rectangle"
        ann_dict["shapes"].append(shape)
        with open(json_save_path, 'w') as jsonFile:
            jsonFile.write(json.dumps(ann_dict,indent=4))

















