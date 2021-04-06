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

def has_file_allowed_extension(filename, extensions):
    """Checks if a file is an allowed extension.

    Args:
        filename (string): path to a file

    Returns:
        bool: True if the filename ends with a known image extension
    """
    filename_lower = filename.lower()#转换字符串中所有大写字符为小写
    return any(filename_lower.endswith(ext) for ext in extensions)

def get_img_info(img, coco, classes, json_dir):
    file_name = img['file_name']
    ann_ids = coco.getAnnIds(imgIds=img['id'], iscrowd=None)
    anns = coco.loadAnns(ann_ids)
    extensions = ['.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif']
    stem, suffix = os.path.splitext(file_name)
    if has_file_allowed_extension(file_name, extensions):
        json_path = os.path.join(json_dir, file_name).replace(suffix, ".json")
    else:
        assert 0,f"error filename {file_name}"
    img_info = {}
    img_info['img'] = file_name
    img_info['imgWidth'] = img['width']
    img_info['imgHeight'] = img['height']
    for ann in anns:
        ann['name'] = classes[ann['category_id']]
    img_info['anns'] = anns
    json_dump(img_info, json_path)


def process(ann_path):
    # img_folder="image"
    json_folder="json"
    # img_dir = os.path.join(os.path.dirname(ann_path), img_folder)
    json_dir = os.path.join(os.path.dirname(ann_path), json_folder)
    check_dir(json_dir)
    coco = COCO(ann_path)
    classes = cati2name(coco)
    img_ids = coco.getImgIds()
    for img_id in img_ids:
        img = coco.loadImgs(img_id)[0]
        get_img_info(img, coco, classes, json_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str,
                        default="../sample/yolo",
                        help='root dir')
    opt = parser.parse_args()
    root=opt.root
    ann_path = "newcar_val.json"
    process(os.path.join(root, ann_path))

