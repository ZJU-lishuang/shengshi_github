import os
import cv2
import shutil
import json
from tqdm import tqdm
from PIL import Image
from pycocotools.coco import COCO
import argparse
from xml.etree import ElementTree as ET
from os import getcwd

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

#创建一级分支object
def create_object(root,label,xi,yi,xa,ya):#参数依次，树根，xmin，ymin，xmax，ymax
    #创建一级分支object
    _object=ET.SubElement(root,'object')
    #创建二级分支
    name=ET.SubElement(_object,'name')
    name.text = str(label)
    # name.text='AreaMissing'
    pose=ET.SubElement(_object,'pose')
    pose.text='Unspecified'
    truncated=ET.SubElement(_object,'truncated')
    truncated.text='0'
    difficult=ET.SubElement(_object,'difficult')
    difficult.text='0'
    #创建bndbox
    bndbox=ET.SubElement(_object,'bndbox')
    xmin=ET.SubElement(bndbox,'xmin')
    xmin.text='%s'%xi
    ymin = ET.SubElement(bndbox, 'ymin')
    ymin.text = '%s'%yi
    xmax = ET.SubElement(bndbox, 'xmax')
    xmax.text = '%s'%xa
    ymax = ET.SubElement(bndbox, 'ymax')
    ymax.text = '%s'%ya

#创建xml文件
def create_tree(image_name,imgWidth,imgHeight):
    global annotation
    # 创建树根annotation
    annotation = ET.Element('annotation')
    #创建一级分支folder
    folder = ET.SubElement(annotation,'folder')
    #添加folder标签内容
    folder.text=('ls')

    #创建一级分支filename
    filename=ET.SubElement(annotation,'filename')
    filename.text=image_name.strip('.jpg')

    #创建一级分支path
    path=ET.SubElement(annotation,'path')
    path.text=getcwd()+'/ls/%s'%image_name#用于返回当前工作目录

    #创建一级分支source
    source=ET.SubElement(annotation,'source')
    #创建source下的二级分支database
    database=ET.SubElement(source,'database')
    database.text='Unknown'

    #创建一级分支size
    size=ET.SubElement(annotation,'size')
    #创建size下的二级分支图像的宽、高及depth
    width=ET.SubElement(size,'width')
    width.text=str(imgWidth)
    height=ET.SubElement(size,'height')
    height.text=str(imgHeight)
    depth = ET.SubElement(size,'depth')
    depth.text = '3'

    #创建一级分支segmented
    segmented = ET.SubElement(annotation,'segmented')
    segmented.text = '0'

def pretty_xml(element, indent, newline, level=0):  # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行
    if element:  # 判断element是否有子元素
        if (element.text is None) or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # else:  # 此处两行如果把注释去掉，Element的text也会另起一行
            # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
    temp = list(element)  # 将element转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        pretty_xml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作


def get_img_info(img, coco, classes, xml_dir):
    file_name = img['file_name']
    ann_ids = coco.getAnnIds(imgIds=img['id'], iscrowd=None)
    anns = coco.loadAnns(ann_ids)
    extensions = ['.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif']
    stem, suffix = os.path.splitext(file_name)
    if has_file_allowed_extension(file_name, extensions):
        xml_path = os.path.join(xml_dir, file_name).replace(suffix, ".xml")
    else:
        assert 0,f"error filename {file_name}"
    img_info = {}
    img_info['img'] = file_name
    imgWidth = img['width']
    imgHeight= img['height']
    create_tree(file_name,imgWidth,imgHeight)
    for ann in anns:
        bbox=ann['bbox']
        label=classes[ann['category_id']]
        left, top, width, height = bbox
        right=left+width
        bottom=top+height
        create_object(annotation, label, left, top, right, bottom)
    tree = ET.ElementTree(annotation)
    root = tree.getroot()  # 得到根元素，Element类
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(xml_path, encoding="utf-8")


def process(ann_path):
    # img_folder="image"
    xml_folder="xml"
    # img_dir = os.path.join(os.path.dirname(ann_path), img_folder)
    xml_dir = os.path.join(os.path.dirname(ann_path), xml_folder)
    check_dir(xml_dir)
    coco = COCO(ann_path)
    classes = cati2name(coco)
    img_ids = coco.getImgIds()
    for img_id in img_ids:
        img = coco.loadImgs(img_id)[0]
        get_img_info(img, coco, classes, xml_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str,
                        default="../data/VOC2028",
                        help='root dir')
    opt = parser.parse_args()
    root=opt.root
    ann_path = "clothing_2classes.json"
    process(os.path.join(root, ann_path))

