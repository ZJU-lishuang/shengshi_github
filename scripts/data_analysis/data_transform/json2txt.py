import os
import glob
import cv2
import json
import numpy as np
import argparse
from tqdm import tqdm

def json_load(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
    return data

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def json2yolo(filename,class_name_path):
    classes_dict = {}
    with open(class_name_path) as f:
        for idx, line in enumerate(f.readlines()):
            class_name = line.strip()
            classes_dict[class_name] = idx

    label_folder="json/"
    image_folder="imageset/"
    txt_folder="txt/"
    newimage_folder="txt_image/"
    
    img_info = json_load(filename)
    width=img_info['imgWidth']
    height=img_info['imgHeight']
    imagename=img_info["img"]
    ignore_box=True
    if ignore_box:
        imagepath = os.path.join(os.path.dirname(filename),imagename).replace(label_folder, image_folder)
        img = cv2.imread(imagepath)  # BGR

    lines = []
    nplines=[]
    for ann in img_info['anns']:
        x, y, w, h = ann['bbox']
        x2=x+w
        y2=y+h
        class_name = ann['name']
        if class_name not in classes_dict:
            # print(f"{class_name} is not in classes_dict")
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
        txt_name = filename.replace(".json", ".txt").replace(label_folder, txt_folder)
        check_dir(os.path.dirname(txt_name))
        with open(txt_name, "w") as f:
            f.writelines(lines)
    if ignore_box:
        save_roiimage_path=imagepath.replace(image_folder, newimage_folder)
        check_dir(os.path.dirname(save_roiimage_path))
        cv2.imwrite(save_roiimage_path, img)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str,
                        default="fangweisui_community",
                        help='root dir')
    opt = parser.parse_args()

    root = opt.root
    json_file_se = "json/*.json"
    class_name_path=os.path.join(root,'classes.names')
    json_file_se = os.path.join(root, json_file_se)
    json_files = glob.glob(json_file_se)
    for json_file in tqdm(json_files):
        json2yolo(json_file,class_name_path)