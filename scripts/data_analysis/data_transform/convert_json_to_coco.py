#coding:utf-8

import json
from functools import reduce
import operator
import argparse
import os
from tqdm import tqdm
import glob
import cv2
 
def parse_args():
    parser = argparse.ArgumentParser(description='Convert dataset')
    parser.add_argument(
        '--dataset', help="dataset type", default='normal', type=str)
    parser.add_argument(
        '--outdir', help="output dir for json files", default='../sample/yolo', type=str)
    parser.add_argument(
        '--datadir', help="data dir for annotations to be converted",
        default='../sample/yolo', type=str)
    return parser.parse_args()

def search(path,filename):
    path_file=[]
    for root,dirs,files in os.walk(path):
        if filename in dirs or filename in files:
            root=str(root)
            re_path=os.path.join(root,filename)
            path_file.append(re_path)
    return path_file

def convert_labelme_json_format(data_dir, out_dir):
    """Convert from labelme format to COCO format """
    #保存的json文件后缀名
    sets = [
         'train'
    ]
    #训练集，测试集，验证集路径
    ann_dirs = [
         'split_folder_for_train'
    ]
    category_name = [
        '汽车',
        '二轮车',
        '三轮车'
    ]
    json_name = 'normal_%s.json'
    img_id = 0
    ann_id = 0
    cat_id = 1
    category_dict = {}

    for i in range(len(category_name)):
        category_dict[category_name[i]]=i

    for data_set in sets:
        print('Starting %s' % data_set)
        ann_dict = {}
        images = []
        annotations = []
        json_file_se="json/*.json"
        json_file_se = os.path.join(data_dir, json_file_se)
        json_files = glob.glob(json_file_se)
        for json_file in tqdm(json_files):
            json_ann = json.load(open(json_file))
            image = {}
            image['id'] = img_id
            img_id += 1

            image['width'] = json_ann['imgWidth']
            image['height'] = json_ann['imgHeight']
            objects_anns = json_ann['anns']
            # base_dir=os.path.dirname(os.path.dirname(json_file))
            # re = search(base_dir, json_ann["img"])
            # image['file_name'] = re[0]
            image_file = json_ann['img']
            image['file_name'] = image_file
            images.append(image)
            for objects_ann in objects_anns:
                object_cls = objects_ann['name']

                ann = {}
                ann['id']=ann_id
                ann_id += 1
                ann['category_id'] = objects_ann['category_id']
                ann['image_id'] = image['id']
                # ann['area']=objects_ann['area']
                ann['iscrowd'] = 0

                assert object_cls in category_dict
                
                # if object_cls in category_name and object_cls not in category_dict:
                #     #0 is for background
                #     category_dict[object_cls]=category_name.index(object_cls)+1
                
                # if object_cls not in category_dict:
                #     category_dict[object_cls] = objects_ann['category_id']
                
                ann['bbox']=objects_ann['bbox']

                annotations.append(ann)
        ann_dict['images'] = images
        category_dict=sorted(category_dict.items(), key=lambda asd: asd[1])
        categories = [{"id": name[1], "name": name[0]} for name in category_dict]
        ann_dict['categories'] = categories
        ann_dict['annotations'] = annotations
        print("Num categories: %s" % len(categories))
        print("Num images: %s" % len(images))
        print("Num annotations: %s" % len(annotations))
        jsFile = os.path.join(out_dir, json_name % data_set)
        with open(jsFile, 'w') as outfile:
            outfile.write(json.dumps(ann_dict, sort_keys=True,ensure_ascii=False))

if __name__ == '__main__':
    args = parse_args()
    if args.dataset == "normal":
        convert_labelme_json_format(args.datadir, args.outdir)
    else:
        print("Dataset not supported: %s" % args.dataset)