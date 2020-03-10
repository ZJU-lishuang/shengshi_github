#coding:utf-8
 
# pip install lxml
 
import sys
import os
import json
import xml.etree.ElementTree as ET
import cv2
 
 
START_BOUNDING_BOX_ID = 1
 
#注意下面的dict存储的是实际检测的类别，需要根据自己的实际数据进行修改
#这里以自己的数据集person和hat两个类别为例，如果是VOC数据集那就是20个类别
#注意类别名称和xml文件中的标注名称一致
PRE_DEFINE_CATEGORIES = {"person": 1}
 
def get(root, name):
    vars = root.findall(name)
    return vars
 
 
def get_and_check(root, name, length):
    vars = root.findall(name)
    if len(vars) == 0:
        raise NotImplementedError('Can not find %s in %s.'%(name, root.tag))
    if length > 0 and len(vars) != length:
        raise NotImplementedError('The size of %s is supposed to be %d, but is %d.'%(name, length, len(vars)))
    if length == 1:
        vars = vars[0]
    return vars
 
 
def get_filename_as_int(filename):
    try:
        filename = os.path.splitext(filename)[0]
        return int(filename)
    except:
        raise NotImplementedError('Filename %s is supposed to be an integer.'%(filename))
 
def subdirs(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir():
            yield entry.name 

def subfiles(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and not entry.is_dir():
            yield entry.name
'''
在生成coco格式的annotations文件之前:
1.执行renameData.py对xml和jpg统一命名；
2.
3.执行splitData方法，切分好对应的train/val/test数据集
'''
if __name__ == '__main__':
    folder_list= ["train","val","test"]
    #注意更改base_dir为本地实际图像和标注文件路径
    base_dir = "/home/lishuang/Disk/shengshi_data/video2image" 
    
    json_dir = base_dir + "/instances_" + "test" + ".json"

    json_dict = {"images":[],  #ls
                 "categories": []}   #ls
    categories = PRE_DEFINE_CATEGORIES
    bnd_id = START_BOUNDING_BOX_ID
    num = 0

    print("json file: ",json_dir)   

    fig_names_all = []
    for dir in subdirs(base_dir):
        FigDirectory = os.path.join(base_dir, dir)

        fig_names = []
        tag = '.jpg'
        for file in subfiles(FigDirectory):
            # for file in os.listdir(DirectoryPath):
            file_path = os.path.join(FigDirectory, file)
            if os.path.splitext(file_path)[1] == tag:
                num +=1
                if num%50==0:
                    print("processing ",num,"; file ",file)
                    
                
                img=cv2.imread(file_path)
                height, width = img.shape[:2]
                # tree = ET.parse(xml_f)
                # root = tree.getroot()
                ## The filename must be a number
                filename = file[:-4]
                #image_id = get_filename_as_int(filename)  #ls
                image_id=num   #ls
                # size = get_and_check(root, 'size', 1)
                # width = int(get_and_check(size, 'width', 1).text)
                # height = int(get_and_check(size, 'height', 1).text)
                # image = {'file_name': filename, 'height': height, 'width': width,
                #          'id':image_id}
                image = {'file_name': (dir+'/'+filename+'.jpg'), 'height': height, 'width': width,
                            'id':image_id}
                json_dict['images'].append(image)



   
    

    for cate, cid in categories.items():
        cat = {'supercategory': 'none', 'id': cid, 'name': cate}
        json_dict['categories'].append(cat)
    json_fp = open(json_dir, 'w')
    json_str = json.dumps(json_dict)
    json_fp.write(json_str)
    json_fp.close()

    