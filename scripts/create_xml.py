#!/usr/bin/python
# -*- coding=utf-8 -*-
# author : Manuel
# date: 2019-05-15

from xml.etree import ElementTree as ET
import numpy as np
# from skimage import data,filters,segmentation,measure,morphology,color
# from scipy.misc import imread
import os
from os import getcwd


IMAGES_LIST=os.listdir('ls')#图片路径

#创建一级分支object
def create_object(root,xi,yi,xa,ya):#参数依次，树根，xmin，ymin，xmax，ymax
    #创建一级分支object
    _object=ET.SubElement(root,'object')
    #创建二级分支
    name=ET.SubElement(_object,'name')
    name.text='AreaMissing'
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
def create_tree(image_name):
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
    width.text='512'
    height=ET.SubElement(size,'height')
    height.text='384'
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


def main():
    for image_name in IMAGES_LIST:
        #只处理jpg文件
        if image_name.endswith('jpg'):
            #将图像通过连通域分割，得到连通域坐标列表，该列表的形式[[a,b,c,d],[e,f,g,h]...,]
            # image = color.rgb2gray(imread(os.path.join(r'./ls', image_name)))
            create_tree(image_name)

            create_object(annotation, 0, 0, 10, 10)
            create_object(annotation, 10, 10, 20, 20)

            # for coordinate_list in coordinates_list:
            #     create_object(annotation, coordinate_list[0], coordinate_list[1], coordinate_list[2], coordinate_list[3])
                # if coordinates_list==[]:
                #     break
            # 将树模型写入xml文件
            tree = ET.ElementTree(annotation)
            # tree.write('ls/%s.xml' % image_name.strip('.jpg'))
            
            # tree = ElementTree.parse('movies.xml')  # 解析movies.xml这个文件
            # root = tree.getroot()  # 得到根元素，Element类
            # pretty_xml(root, '\t', '\n')  # 执行美化方法
            tree.write('ls/%s.xml' % image_name.strip('.jpg'))



if __name__ == '__main__':
    main()