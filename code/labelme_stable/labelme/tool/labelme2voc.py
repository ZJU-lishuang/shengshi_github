# -*- coding:utf-8 -*-
# 将自己定义好的json格式转化为VOC格式的xml
import cv2
import xml.dom.minidom

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from xml.etree.ElementTree import Element, SubElement
import os
import argparse
import sys
from xml.dom.minidom import parseString
from lxml import etree
import json
import xmltodict
import dicttoxml
import os

path = os.path.abspath('.')


def parse_args():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(description='**********')
    parser.add_argument('--xml', dest='xml', type=str)
    # parser.add_argument('--classes', dest='classes',type=list)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    return args


def del_nobe(xmlname, name):
    tree, root = read_xml(xmlname)
    for obj in root.getchildren():
        if obj.tag == 'objects':
            # print obj.find('name').text.strip()
            # print type(obj.find('name').text)
            if obj.find('name').text.strip() not in name:
                # print 'is watch'
                root.remove(obj)
                tree.write(filename, "utf-8")
                write_xml(tree, xmlname)


def del_xml_file(xmlname):
    tree, root = read_xml(xmlname)
    obj = root.findall('object')
    print(len(obj))
    if len(obj) == 0:
        os.remove(xmlname)
        print(xmlname, '  had delete! ')


def read_xml(xmlname):
    '''读取并解析xml文件
      in_path: xml路径
      return: ElementTree'''
    tree = ET.parse(xmlname)
    root = tree.getroot()
    return tree, root


def write_xml(tree, out_path):
    '''将xml文件写出
      tree: xml树
      out_path: 写出路径'''
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    # tree.write(out_path, pretty_print=True, xml_declaration=True, encoding='utf-8')


def create_node(tag, content):
    '''''新造一个节点
       tag:节点标签
       property_map:属性及属性值map
       content: 节点闭合标签里的文本内容
       return 新节点'''
    element = Element(tag)
    element.text = content
    return element


def add_child_node(nodelist, element):
    '''''给一个节点添加子节点
       nodelist: 节点列表
       element: 子节点'''
    for node in nodelist:
        node.append(element)


def find_nodes(tree, path):
    '''''查找某个路径匹配的所有节点
       tree: xml树
       path: 节点路径'''
    return tree.findall(path)


def del_node_by_tagkeyvalue(nodelist, tag):
    '''''同过属性及属性值定位一个节点，并删除之
       nodelist: 父节点列表
       tag:子节点标签
       kv_map: 属性及属性值列表'''
    for parent_node in nodelist:
        children = parent_node.getchildren()
        for child in children:
            if child.tag in tag:
                parent_node.remove(child)


def modify(xmlfile):
    tree, root = read_xml(xmlfile)
    objs = tree.findall('object')
    file_name = os.path.splitext(filename)[0]
    FileName = SubElement(root, 'filename')
    FileName.text = file_name
    for obj in objs:
        # obj.text = 'object'
        bbox = obj.findall('bbox')
        print("bbox: ", bbox)
        list1 = bbox[0].text
        list2 = bbox[1].text
        list1_val = ''.join([c for c in list1 if c in '1234567890,'])
        list2_val = ''.join([c for c in list2 if c in '1234567890,'])
        target_list1 = list1_val.split(",")
        target_list2 = list2_val.split(",")
        xmin_val = target_list1[0]
        ymin_val = target_list1[1]
        xmax_val = target_list2[0]
        ymax_val = target_list2[1]

        bndbox = SubElement(obj, 'bndbox')
        # xmin = create_node("xmim", str(int(xmin_val)))
        # bndbox.append(xmin)
        # ymin = create_node('ymin', str(int(ymin_val)))
        # bndbox.append(ymin)
        # xmax = create_node('xmax', str(int(xmax_val)))
        # bndbox.append(xmax)
        # ymax = create_node('ymax', str(int(ymax_val)))
        # bndbox.append(ymax)

        xmin = SubElement(bndbox, 'xmin')
        xmin.text = str(int(xmin_val))
        ymin = SubElement(bndbox, 'ymin')
        ymin.text = str(int(ymin_val))
        xmax = SubElement(bndbox, 'xmax')
        xmax.text = str(int(xmax_val))
        ymax = SubElement(bndbox, 'ymax')
        ymax.text = str(int(ymax_val))

        name = SubElement(obj, 'name')
        name.text = obj.find('label').text

    # 定位父节点
    del_parent_nodes = find_nodes(tree, "object")
    # 准确定位子节点并删除之
    del_node_by_tagkeyvalue(del_parent_nodes, "bbox")
    del_node_by_tagkeyvalue(del_parent_nodes, "label")

    write_xml(tree, xmlfile)


# json转xml函数
def jsontoxml(jsonstr, file_path):
    # xmltodict库的unparse()json转xml
    print("len(jsonstr) = ", len(jsonstr))
    xmlstr = xmltodict.unparse(jsonstr)
    print("xmlstr: ", xmlstr)
    dom = parseString(xmlstr)
    xml = dom.toprettyxml(indent="  ")
    xml_path = os.path.splitext(file_path)[0] + '.xml'
    with open(xml_path, 'w') as f:
        f.write(xml)
        f.close()


if __name__ == '__main__':
    # args = parse_args()
    # print('Called with args:')
    # print(args)

    num = 0

    # 将json转换成xml
    cnt = 0
    JSON_file = {}
    json_path = "/home/shining/Projects/work/detectron.pytorch/vis_outputs/json"
    xml_path = ""
    for root, dirs, files in os.walk(json_path):
        for file in files:
            file_path = os.path.join(root, file)
            src = open(file_path)
            jsonstr = json.loads(src.read())
            jsonstr.update(object=jsonstr.pop('objects'))
            if len(jsonstr) != 1:
                JSON_file["annotation"] = jsonstr
            cnt += 1
            print("json num = ", cnt)
            if isinstance(JSON_file, dict):
                jsontoxml(JSON_file, file_path)
    # for filename in os.listdir():

    for filename in os.listdir(json_path):
        print(os.path.join(json_path, filename))
        if os.path.splitext(filename)[1] == '.xml':
            file_path = os.path.join(json_path, filename)
            modify(file_path)

    print("Done")
