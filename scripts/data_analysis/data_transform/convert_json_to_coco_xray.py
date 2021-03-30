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
        '--dataset', help="dataset type", default='xray', type=str)
    parser.add_argument(
        '--outdir', help="output dir for json files", default='/home/lishuang/Disk/gitlab/traincode/CenterNet2/script', type=str)
    parser.add_argument('--task_id', type=int,
                        default=[503,517,525,526,527,528,529,530,531,532,541,543,544,555,556,557,558,9999],
                        # default=[8],
                        help='task_id for xray')
    parser.add_argument(
        '--datadir', help="data dir for annotations to be converted",
        default='/home/lishuang/Disk/gitlab/traincode/CenterNet2/datasets/xray', type=str)
    return parser.parse_args()

def search(path,filename):
    path_file=[]
    for root,dirs,files in os.walk(path):
        if filename in dirs or filename in files:
            root=str(root)
            re_path=os.path.join(root,filename)
            path_file.append(re_path)
    
    return path_file

def convert_labelme_json_format(data_dir,id_list, out_dir):
    """Convert from labelme format to COCO person format - keypoint"""
    #保存的json文件后缀名
    sets = [
         'train'
    ]
    #训练集，测试集，验证集路径
    ann_dirs = [
         'split_folder_for_train'
    ]
    category_keypoints = [
        'person'
    ]
    json_name = 'xray_%s.json'
    ends_in = '.json'
    img_id = 0
    ann_id = 0
    cat_id = 1
    category_dict = {}
    for data_set in sets:
        print('Starting %s' % data_set)
        ann_dict = {}
        images = []
        annotations = []
        for task_id in tqdm(id_list):
            json_file_se="%s/json/*.json" % task_id
            json_file_se = os.path.join(data_dir, json_file_se)
            json_files = glob.glob(json_file_se)
            for json_file in tqdm(json_files):
                json_ann = json.load(open(json_file))
                image = {}
                image['id'] = img_id
                img_id += 1

                if 'imgWidth' not in json_ann:
                    img_path=json_file.replace('.json','.jpg').replace('json/','imageset/')
                    cur_image = cv2.imread(img_path)
                    h,w,c=cur_image.shape
                    image['width']=w
                    image['height']=h
                    image_file = f"{task_id}/imageset/{json_ann['img']}"
                    image['file_name'] = image_file
                    images.append(image)
                    object_cls = json_ann['name']
                    ann = {}
                    ann['id'] = ann_id
                    ann_id += 1
                    ann['category_id'] = category_dict[object_cls]
                    ann['image_id'] = image['id']
                    ann['area'] = w*h
                    ann['iscrowd'] = 0

                    ann['bbox'] = json_ann['box']

                    annotations.append(ann)
                    continue
                else:
                    image['width'] = json_ann['imgWidth']
                    image['height'] = json_ann['imgHeight']
                objects_anns = json_ann['anns']
                # base_dir=os.path.dirname(os.path.dirname(json_file))
                # re = search(base_dir, json_ann["img"])
                # image['file_name'] = re[0]
                image_file = f"{task_id}/imageset/{json_ann['img']}"
                image['file_name'] = image_file
                images.append(image)
                for objects_ann in objects_anns:
                    object_cls = objects_ann['name']

                    ann = {}
                    ann['id']=ann_id
                    ann_id += 1
                    ann['category_id'] = objects_ann['category_id']
                    ann['image_id'] = image['id']
                    ann['area']=objects_ann['area']
                    ann['iscrowd'] = 0
                    if object_cls not in category_dict:
                        category_dict[object_cls] = objects_ann['category_id']
                    # if objects_ann['category_id'] not in category_dict:
                    #     category_dict[objects_ann['category_id']] = objects_ann['category_id']

                    ann['bbox']=objects_ann['bbox']

                    annotations.append(ann)
        ann_dict['images'] = images
        category_dict=sorted(category_dict.items(), key=lambda asd: asd[1])
        # categories = [{"id": category_dict[name], "name": name} for name in category_dict]
        categories = [{"id": name[1], "name": name[0]} for name in category_dict]
        # categories[0]['supercategory'] = 'xray'
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
    if args.dataset == "xray":
        convert_labelme_json_format(args.datadir,args.task_id, args.outdir)
    else:
        print("Dataset not supported: %s" % args.dataset)