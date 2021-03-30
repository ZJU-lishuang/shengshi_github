import numpy as np
import os
import glob
from tqdm import tqdm
import json
from pycocotools.coco import COCO

def main():
    root = "/home/lishuang/Disk/shengshi_github/scripts/data_analysis/sample/yolo"
    pred_json="result.json"
    pred_json=os.path.join(root,pred_json)
    val_json="newcar_val.json"
    val_json=os.path.join(root,val_json)
    inference_label="autolabels"

    cocoval = COCO(val_json)
    img_dict={}
    img_wh_dict={}
    for img_id in cocoval.imgs:
        single_img=cocoval.imgs[img_id]
        img_dict[single_img['file_name']]=single_img['id']
        img_wh_dict[single_img['file_name']]=[single_img["width"],single_img['height']]
    txt_file_se = f"{inference_label}/*.txt"
    txt_file_se = os.path.join(root, txt_file_se)
    txt_files = glob.glob(txt_file_se)
    jdict=[]
    for txt_file in tqdm(txt_files):
        img_name=os.path.basename(txt_file).replace(".txt",".jpg")
        img_id=img_dict[img_name]
        w,h=img_wh_dict[img_name]
        with open(txt_file, 'r') as f:
            l = np.array([x.split() for x in f.read().strip().splitlines()], dtype=np.float32)  # labels
        if len(l):
            assert l.shape[1] == 6, 'labels require 5 columns each'
            assert (l >= 0).all(), 'negative labels'
            assert (l[:, 1:] <= 1).all(), 'non-normalized or out of bounds coordinate labels'
            assert np.unique(l, axis=0).shape[0] == l.shape[0], 'duplicate labels'
        else:
            l = np.zeros((0, 6), dtype=np.float32)

        for single_l in l:
            class_idx = int(single_l[0])
            cx, cy, bw, bh = single_l[2:]
            box = np.array([cx * w, cy * h, w * bw, h * bh])
            box[:2] -= box[2:] / 2  # xy center to top-left corner
            jdict.append({'image_id': img_id,
                          'category_id': class_idx,
                          'bbox': [round(x, 3) for x in box],
                          'score': round(single_l[1].tolist(), 5)})
    with open(pred_json, 'w') as f:
        json.dump(jdict, f)

if __name__ == '__main__':
    main()