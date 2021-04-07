import numpy as np
import os
import glob
from tqdm import tqdm
import cv2
import json

def xyxy2xywh(x):
    # Convert nx4 boxes from [x1, y1, x2, y2] to [x, y, w, h] where xy1=top-left, xy2=bottom-right
    y = np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2  # x center
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2  # y center
    y[:, 2] = x[:, 2] - x[:, 0]  # width
    y[:, 3] = x[:, 3] - x[:, 1]  # height
    return y

def main():
    root="../sample/yolo"
    # file list
    train_file = "../sample/yolo/train.txt"
    #class
    class_all_name="../sample/yolo/classes.names"
    image_folder="image/"
    txt_folder="labels/"

    with open(class_all_name, 'r') as f:
        names = np.array([x for x in f.read().strip().splitlines()], dtype=np.str)  # labels

    f = []
    with open(train_file, 'r') as t:
        t = t.read().strip().splitlines()
        f += [x for x in t]  # local to global path

    img_files=f

    data_set="val"
    json_name = 'newcar_%s.json'
    img_id = 0
    ann_id = 0
    category_dict = {}
    for i in range(len(names)):
        category_dict[names[i]]=i
    ann_dict={}
    images = []
    annotations = []
    for img_file in tqdm(img_files):
        img_name=os.path.basename(img_file)
        stem, suffix = os.path.splitext(img_name)
        txt_file=img_file.replace(suffix,".txt").replace(image_folder,txt_folder)
        cur_image = cv2.imread(img_file)
        h,w,c=cur_image.shape
        image = {}
        image['id'] = img_id
        img_id += 1
        image['width'] = w
        image['height'] = h
        image['file_name'] = img_name
        images.append(image)
        with open(txt_file, 'r') as f:
            l = np.array([x.split() for x in f.read().strip().splitlines()], dtype=np.float32)  # labels
        if len(l):
            assert l.shape[1] == 5, 'labels require 5 columns each'
            assert (l >= 0).all(), 'negative labels'
            assert (l[:, 1:] <= 1).all(), 'non-normalized or out of bounds coordinate labels'
            assert np.unique(l, axis=0).shape[0] == l.shape[0], 'duplicate labels'
        else:
            l = np.zeros((0, 5), dtype=np.float32)
        for single_l in l:
            class_idx=int(single_l[0])
            object_cls=names[class_idx]
            ann = {}
            ann['id'] = ann_id
            ann_id += 1
            ann['category_id'] = class_idx
            ann['image_id'] = image['id']
            ann['iscrowd'] = 0
            assert object_cls in category_dict
            # if object_cls not in category_dict:
            #     category_dict[object_cls] = class_idx
            cx,cy,bw,bh=single_l[1:]
            box=np.array([cx*w,cy*h,w*bw,h*bh])
            box[:2] -= box[2:] / 2  # xy center to top-left corner
            box=[round(x, 3) for x in box]
            ann['bbox'] = box
            annotations.append(ann)

    ann_dict['images'] = images
    category_dict = sorted(category_dict.items(), key=lambda asd: asd[1])
    # categories = [{"id": category_dict[name], "name": name} for name in category_dict]
    categories = [{"id": name[1], "name": name[0]} for name in category_dict]
    # categories[0]['supercategory'] = 'xray'
    ann_dict['categories'] = categories
    ann_dict['annotations'] = annotations
    print("Num categories: %s" % len(categories))
    print("Num images: %s" % len(images))
    print("Num annotations: %s" % len(annotations))
    jsFile = os.path.join(root, json_name % data_set)
    with open(jsFile, 'w') as outfile:
        outfile.write(json.dumps(ann_dict, sort_keys=True, ensure_ascii=False))

if __name__ == '__main__':
    main()