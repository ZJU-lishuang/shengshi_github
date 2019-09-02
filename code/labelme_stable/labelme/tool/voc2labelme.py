# -*- coding:utf-8 -*-
#
#目前未实现
#
#
from lxml import etree
import xmltodict
from xml.dom.minidom import parseString
import json
import argparse
import sys
import os
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

XML_EXTENSIONS = ['.xml']
def is_xml_file(filename):
    """Checks if a file is an image.
      Args:
          filename (string): path to a file
      Returns:
          bool: True if the filename ends with a known image extension
    """
    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in XML_EXTENSIONS)



#定义xml转json的函数
def xmltojson(xmlpath):
    xmlfile = etree.parse(xmlpath)
    xmlstr = etree.tostring(xmlfile)
    #parse是的xml解析器
    xmlparse = xmltodict.parse(xmlstr)
    #json库dumps()是将dict转化成json格式，loads()是将json转化成dict格式。
    #dumps()方法的ident=1，格式化json
    # jsonstr = json.dumps(xmlparse,indent=1)
    print ("xmlparse: ", xmlparse)
    jsonstr = json.dumps(xmlparse)
    print("xml2json: ", jsonstr)
    print("len(jsonstr) = ", len(jsonstr))
    jsonstr = jsonstr.replace("\\", "/")
    print("xml2json replace: ", jsonstr)
    __version__= ""
    otherData = {}
    flags = {}
    # data = dict(
    #     version=__version__,
    #     flags=flags,
    #     objects=shapes,
    #     lineColor=lineColor,
    #     fillColor=fillColor,
    #     filename=os.path.basename(imagePath),
    #     imageData=imageData,
    #     imgHeight=imgHeight,
    #     imgWidth=imgWidth,
    # )
    # for key, value in otherData.items():
    #     data[key] = value
    # try:
    #     with open(filename, 'wb' if PY2 else 'w') as f:
    #         json.dump(data, f, ensure_ascii=False, indent=2)
    #     self.filename = filename
    # except Exception as e:
    #     raise LabelFileError(e)        if imageData is not None:
    #         imageData = base64.b64encode(imageData).decode('utf-8')
    #         imgHeight, imgWidth = self._check_image_height_and_width(
    #             imageData, imgHeight, imgWidth
    #         )
    #     if otherData is None:
    #         otherData = {}
    #     if flags is None:
    #         flags = {}
    #     data = dict(
    #         version=__version__,
    #         flags=flags,
    #         objects=shapes,
    #         lineColor=lineColor,
    #         fillColor=fillColor,
    #         filename=os.path.basename(imagePath),
    #         imageData=imageData,
    #         imgHeight=imgHeight,
    #         imgWidth=imgWidth,
    #     )
    #     for key, value in otherData.items():
    #         data[key] = value
    #     try:
    #         with open(filename, 'wb' if PY2 else 'w') as f:
    #             json.dump(data, f, ensure_ascii=False, indent=2)
    #         self.filename = filename
    #     except Exception as e:
    #         raise LabelFileError(e)
    absolute_json_path = "/home/eric/Disk/testyolov2/gtxml-2/2017Y09M02D16H5_xml2json.json"
    with open(absolute_json_path, "w") as f:
        json.dump(xmlparse, f, sort_keys=True, indent=2)



if __name__ == '__main__':
    # args = parse_args()
    # print('Called with args:')
    # print(args)

    num = 0

    # 将json转换成xml
    cnt = 0
    JSON_file = {}
    json_path = "/home/shining/Projects/datasets/VOCdevkit/CAR/Annotations"
    xml_path = ""
    for root, dirs, files in os.walk(json_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_xml_file(file_path):
                xmltojson(file_path)
    # for filename in os.listdir():

    print("Done")
