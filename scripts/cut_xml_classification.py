import xml.etree.ElementTree as ET
import pickle
import os
from os import listdir, getcwd
from os.path import join
from PIL import Image
import cv2
import xml.dom.minidom

class boxstru:
    def __init__(self):
        self.xmin   = 0.0
        self.xmax   = 0.0
        self.ymin   = 0.0
        self.ymax   = 0.0
        self.name   = ''


class xmlstru:

    def __init__(self):
        self.name   = ''  # 检测图片文件夹
        self.width  = 0.0  # 生成结果图像保存文件夹
        self.height = 0.0  # 生成xml保存文件夹
        self.depth  = 0.0  # 统计结果
        self.box    = []

def ReadXml(xmlfile ):
    value =xmlstru()
    dom = xml.dom.minidom.parse(xmlfile)#read XML 文档
    root = dom.documentElement          #get the XML document object

    value.name = root.getElementsByTagName('filename')

    sizes = root.getElementsByTagName("size")#找到XML文档中所有<size>的值
    for sizetmp in sizes:
        tmp = sizetmp.getElementsByTagName('width')[0]
        value.width = int(tmp.childNodes[0].nodeValue)

        tmp = sizetmp.getElementsByTagName('height')[0]
        value.height = int(tmp.childNodes[0].nodeValue)

        tmp = sizetmp.getElementsByTagName('depth')[0]
        value.depth = int(tmp.childNodes[0].nodeValue)


    #修改
    objs = root.getElementsByTagName("object")
    for obj in objs:
        boxstr = boxstru()

        tmp = obj.getElementsByTagName('xmin')[0]
        boxstr.xmin = int( float(tmp.childNodes[0].nodeValue))

        tmp = obj.getElementsByTagName('ymin')[0]
        boxstr.ymin = int( float(tmp.childNodes[0].nodeValue))

        tmp = obj.getElementsByTagName('xmax')[0]
        boxstr.xmax = int( float(tmp.childNodes[0].nodeValue))

        tmp = obj.getElementsByTagName('ymax')[0]
        boxstr.ymax = int( float(tmp.childNodes[0].nodeValue))

        tmp = obj.getElementsByTagName('name')[0]
        boxstr.name = tmp.childNodes[0].nodeValue

        value.box.append(boxstr)

    return value

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def cut_xml(fig_names_all,xml_names_all,save_roiimage_paths):
    fig_num=len(fig_names_all)
    for i in range(len(fig_names_all)):
        xml_name = xml_names_all[i] # get absolute directory of relevant XML file's
        if not os.path.exists(xml_name):
            continue

        files = os.path.basename(fig_names_all[i])  # get file name
        imagename = os.path.splitext(files)[0]  # file's name
        print("id:",os.getpid()," [{}/{}] :".format(i+1,fig_num),imagename)


        fig = cv2.imread(fig_names_all[i])
        height,width,_=fig.shape


        value = ReadXml(xml_name)  # read XML file from original directory
        boxnum=0
        for ibox in range(len(value.box)):
            xmin = value.box[ibox].xmin
            ymin =  value.box[ibox].ymin
            xmax = value.box[ibox].xmax
            ymax = value.box[ibox].ymax
            name=value.box[ibox].name
            boxnum=boxnum+1

            bheight=ymax-ymin
            bwidth=xmax-xmin

            scalexmin=xmin-0.5*bwidth
            scaleymin=ymin-0.5*bheight
            scalexmax=xmax+0.5*bwidth
            scaleymax = ymax + 0.5 * bheight

            bxmin=max(0,int(scalexmin))
            bymin=max(0,int(scaleymin))
            bxmax=min(width,int(scalexmax))
            bymax=min(height,int(scaleymax))


            roi_image = fig[bymin:bymax, bxmin:bxmax]

            roi_image_name=imagename+'img_'+str(boxnum)+'_'+name+'.jpg'

            check_dir(os.path.join(save_roiimage_paths,name))

            save_roiimage_path=os.path.join(save_roiimage_paths,name,roi_image_name)

            cv2.imwrite(save_roiimage_path, roi_image)

def subfiles(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and not entry.is_dir():
            yield entry.name

if __name__ == '__main__':
    imgpath="/home/lishuang/Disk/shengshi_data/new_anti_tail/JPEGImages"
    xmlpath="/home/lishuang/Disk/shengshi_data/new_anti_tail/Annotations"
    savepath="/home/lishuang/Disk/shengshi_data/new_anti_tail/classification"
    tag='.jpg'
    fig_names=[]
    xmldirs=[]
    for file in subfiles(imgpath):
        # for file in os.listdir(DirectoryPath):
        file_path = os.path.join(imgpath, file)
        if os.path.splitext(file_path)[1] == tag:
            fig_names.append(file_path)

            files = os.path.basename(file_path)  # get file name
            filename = os.path.splitext(files)[0]  # file's name
            xmldir = os.path.join(xmlpath, filename + '.xml')
            xmldirs.append(xmldir)


    cut_xml(fig_names,xmldirs,savepath)