import os
import cv2
import shutil
import json
from tqdm import tqdm
from PIL import Image
from pycocotools.coco import COCO
import argparse

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def json_dump(data, json_out):
    json.dump(data, open(json_out, "w"), indent=2, ensure_ascii=False)


def cati2name(coco):
    classes = dict()
    for cat in coco.dataset['categories']:
        classes[cat['id']] = cat['name']
    return classes


def get_img_info(img, coco, classes, img_dir):
    file_name = img['file_name']
    file_path = os.path.join(img_dir, file_name)
    cur_image = cv2.imread(file_path)
    ann_ids = coco.getAnnIds(imgIds=img['id'], iscrowd=None)
    anns = coco.loadAnns(ann_ids)
    json_path = file_path.replace(".jpg", ".json").replace("imageset/","json/")
    img_info = {}
    img_info['img'] = file_name
    img_info['imgWidth'] = img['width']
    img_info['imgHeight'] = img['height']
    for ann in anns:
        try:
            # 这里是数据平台的数据库有一个bug,有些task没有433的标签
            if ann['category_id'] == 433:
                ann['name'] = "折叠刀"
            else:
                ann['name'] = classes[ann['category_id']]
        except:
            top
            import pdb;
            pdb.set_trace()
    img_info['anns'] = anns
    json_dump(img_info, json_path)


def process(ann_path):
    img_dir = os.path.join(os.path.dirname(ann_path), 'imageset')
    json_dir = os.path.join(os.path.dirname(ann_path), 'json')
    check_dir(json_dir)
    coco = COCO(ann_path)
    classes = cati2name(coco)
    img_ids = coco.getImgIds()
    for img_id in img_ids:
        img = coco.loadImgs(img_id)[0]
        get_img_info(img, coco, classes, img_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str,
                        default="/home/lishuang/Disk/gitlab/traincode/CenterNet2/datasets/xray",
                        help='root dir')
    opt = parser.parse_args()
    root=opt.root
    ann_path = "instances_default.json"
    process(os.path.join(root, ann_path))

