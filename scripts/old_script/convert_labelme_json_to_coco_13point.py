#coding:utf-8

import json
from functools import reduce
import operator
import argparse
import os
 
def parse_args():
    parser = argparse.ArgumentParser(description='Convert dataset')
    parser.add_argument(
        '--dataset', help="person_keypoints", default='person_keypoints', type=str)
    parser.add_argument(
        '--outdir', help="output dir for json files", default='/home/lishuang/Disk/pytorch', type=str)
    parser.add_argument(
        '--datadir', help="data dir for annotations to be converted",
        default='/home/lishuang/Disk/shengshi_data/', type=str)
    # if len(sys.argv) == 1:
    #     parser.print_help()
    #     sys.exit(1)
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
    """Convert from labelme format to COCO person format - keypoint"""
    #保存的json文件后缀名
    sets = [
         'train'
    ]
    #训练集，测试集，验证集路径
    ann_dirs = [
         'keypoint_train13'
    ]
    category_keypoints = [
        'person'
    ]
    json_name = 'person_keypoints_%s.json'
    ends_in = '.json'
    img_id = 0
    ann_id = 0
    cat_id = 1
    category_dict = {}
    file_data=""
    for data_set, ann_dir in zip(sets, ann_dirs):
        print('Starting %s' % data_set)
        ann_dict = {}
        images = []
        annotations = []
        ann_dir = os.path.join(data_dir, ann_dir)
        for root, _, files in os.walk(ann_dir):
            for filename in files:
                if filename.endswith(ends_in):
                    if len(images) % 50 == 0:
                        print("Processed %s images, %s annotations" % (len(images), len(annotations)))
                    json_ann = json.load(open(os.path.join(root, filename)))
                    image = {}
                    image['id'] = img_id
                    img_id += 1

                    image['width'] = json_ann['imgWidth']
                    image['height'] = json_ann['imgHeight']
                    objects_anns = json_ann['objects']
                    #使用root.replace(ann_dir,'')添加子路径
                    re=search(ann_dir,filename[:-(5)] + '.jpg')
                    #安全隐患：此处还应该检查re的长度，查看是否有同名文件在不同文件夹，
                    #或者修改search函数中的ann_dir路径为root路径，并对root路径返回上一级，
                    #这里要根据文件组织结构来进行相应处理
                    image['file_name'] = (re[0].replace(ann_dir+'/',''))
                    images.append(image)

                    for objects_ann in objects_anns:
                        object_cls=objects_ann['label'] 
                        if object_cls not in category_keypoints:
                            continue  # skip non-instance categories
                        keypoints = [p[2] for p in objects_ann['keypoints'] if len(p)==3]
                        numkeypoints=len(keypoints)-keypoints.count(0)
                        if numkeypoints==0:
                            file_data+=image['file_name']+'\n'
                            continue
                        assert numkeypoints!=0,'{}'.format(image['file_name'] )
                        ann = {}
                        ann['id'] = ann_id
                        ann_id += 1
                        ann['image_id'] = image['id']
                        ann['num_keypoints'] = numkeypoints
                        ann['keypoints'] = reduce(operator.add,objects_ann['keypoints'][2:])
                        ann['iscrowd'] =0
                        

                        if object_cls not in category_dict:
                                category_dict[object_cls] = cat_id
                                cat_id += 1
                        ann['category_id'] = category_dict[object_cls]
                        x1=min(objects_ann['keypoints'][0][0],objects_ann['keypoints'][1][0])
                        y1=min(objects_ann['keypoints'][0][1],objects_ann['keypoints'][1][1])
                        x2=max(objects_ann['keypoints'][0][0],objects_ann['keypoints'][1][0])
                        y2=max(objects_ann['keypoints'][0][1],objects_ann['keypoints'][1][1])
                        x=x1
                        y=y1
                        w=x2-x1
                        h=y2-y1
                        ann['bbox']=[x,y,w,h]

                        annotations.append(ann)
        ann_dict['images'] = images
        categories = [{"id": category_dict[name], "name": name} for name in category_dict]
        categories[0]['supercategory']='person'
        categories[0]['keypoints']=['head',
                  'right_shoulder','right_elbow','right_hand','right_buttocks','right_knee','right_foot',
                  'left_shoulder','left_elbow','left_hand','left_buttocks','left_knee','left_foot']
        categories[0]['skeleton']=[[0,1],[1,2],[1,7],[2,3],[1,4],[4,5],[5,6],[0,7],[7,8],[8,9],[7,10],[4,10],[10,11],[11,12]]
        ann_dict['categories'] = categories
        ann_dict['annotations'] = annotations
        print("Num categories: %s" % len(categories))
        print("Num images: %s" % len(images))
        print("Num annotations: %s" % len(annotations))
        jsFile = os.path.join(out_dir, json_name % data_set)
        print("jsFile=",jsFile)
        with open(jsFile, 'w') as outfile:
            outfile.write(json.dumps(ann_dict, sort_keys=True))
    with open('checklist.txt','w') as f:
        f.write(file_data)

                        

                    


if __name__ == '__main__':
    args = parse_args()
    if args.dataset == "person_keypoints":
        convert_labelme_json_format(args.datadir, args.outdir)
    else:
        print("Dataset not supported: %s" % args.dataset)