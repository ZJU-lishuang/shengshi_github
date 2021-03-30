#coding=utf-8
import cv2
import os
import xml.dom.minidom

partname = ""
import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

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

###############loadAllTagFile##############
def loadAllTagFile( DirectoryPath, tag ):# download all files' name
    result = []
    for file in os.listdir(DirectoryPath):
        file_path = os.path.join(DirectoryPath, file)
        if os.path.splitext(file_path)[1] == tag:
            result.append(file_path)
    return result

###############check_dir##############
def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

###############CreatXml##############
def CreatXml(img, results, xmlPath):
   # img = cv2.imread(imgPath)
    imgSize = img.shape
   # imgName = imgPath.split('/')[-1]

    impl = xml.dom.minidom.getDOMImplementation()
    dom = impl.createDocument(None, 'annotation', None)
    root = dom.documentElement

    folder = dom.createElement('folder')
    root.appendChild(folder)
    name_folfer = dom.createTextNode('Unknown')
    folder.appendChild(name_folfer)

    filename = dom.createElement('filename')
    root.appendChild(filename)
   # name_img = dom.createTextNode(os.path.splitext(imgName)[0])
   # filename.appendChild(name_img)

    filepath = dom.createElement('path')
    root.appendChild(filepath)
    #path_img = dom.createTextNode(imgPath)
   # filepath.appendChild(path_img)

    source = dom.createElement('source')
    root.appendChild(source)
    database = dom.createElement('database')
    database_name = dom.createTextNode('Unknown')
    database.appendChild(database_name)
    source.appendChild(database)

    img_size = dom.createElement('size')
    root.appendChild(img_size)
    width = dom.createElement('width')
    width_num = dom.createTextNode(str(int(imgSize[1])))
    width.appendChild(width_num)
    height = dom.createElement('height')
    height_num = dom.createTextNode(str(int(imgSize[0])))
    height.appendChild(height_num)
    depth = dom.createElement('depth')
    depth_num = dom.createTextNode(str(int(imgSize[2])))
    depth.appendChild(depth_num)
    img_size.appendChild(width)
    img_size.appendChild(height)
    img_size.appendChild(depth)

    segmented = dom.createElement('segmented')
    root.appendChild(segmented)
    segmented_num = dom.createTextNode('0')
    segmented.appendChild(segmented_num)

    for i in range(len(results)):
        img_object = dom.createElement('object')
        root.appendChild(img_object)
        label_name = dom.createElement('name')
        namecls = dom.createTextNode(results[i][4])
        label_name.appendChild(namecls)
        pose = dom.createElement('pose')
        pose_name = dom.createTextNode('Unspecified')
        pose.appendChild(pose_name)
        truncated = dom.createElement('truncated')
        truncated_num = dom.createTextNode('0')
        truncated.appendChild(truncated_num)
        difficult = dom.createElement('difficult')
        difficult_num = dom.createTextNode('0')
        difficult.appendChild(difficult_num)
        bndbox = dom.createElement('bndbox')
        xmin = dom.createElement('xmin')
        # xmin_num = dom.createTextNode(str(int(results[i][0])))
        xmin_num = dom.createTextNode(str(int(round(results[i][0] ))))
        xmin.appendChild(xmin_num)
        ymin = dom.createElement('ymin')
        ymin_num = dom.createTextNode(str(int(round(results[i][1] ))))
        ymin.appendChild(ymin_num)
        xmax = dom.createElement('xmax')
        xmax_num = dom.createTextNode(str(int(round(results[i][2] ))))
        xmax.appendChild(xmax_num)
        ymax = dom.createElement('ymax')
        ymax_num = dom.createTextNode(str(int(round(results[i][3] ))))
        ymax.appendChild(ymax_num)
        bndbox.appendChild(xmin)
        bndbox.appendChild(ymin)
        bndbox.appendChild(xmax)
        bndbox.appendChild(ymax)
        img_object.appendChild(label_name)
        img_object.appendChild(pose)
        img_object.appendChild(truncated)
        img_object.appendChild(difficult)
        img_object.appendChild(bndbox)

    f = open(xmlPath, 'w')
    dom.writexml(f, addindent='  ', newl='\n')
    f.close()

##################################################
def annalysisOverlap(roi_box,xml_box):

    h = xml_box.ymax - xml_box.ymin
    w = xml_box.xmax - xml_box.xmin
    area_origin = h * w *1.0
    rate = 0.0
    id = 'none'
    if((xml_box.ymin > roi_box.ymin) & (xml_box.ymax < roi_box.ymax)):
        rate = 1.0
        id = 'in'

    if(( xml_box.ymin < roi_box.ymin) & (xml_box.ymax >roi_box.ymax)):
        rate = 1.0
        id = 'big'

    if((xml_box.ymin < roi_box.ymin) & (xml_box.ymax >roi_box.ymin)): #up
        h1 = xml_box.ymax-roi_box.ymin
        area_new = h1*w*1.0
        rate = area_new/area_origin
        id = 'up'

    if((xml_box.ymax >roi_box.ymax) & (xml_box.ymin < roi_box.ymax)): #down
        h1 = roi_box.ymax-xml_box.ymin
        area_new = h1*w*1.0
        rate = area_new/area_origin
        id = 'down'

    if((xml_box.ymax < roi_box.ymin) | (xml_box.ymin > roi_box.ymax)):#out
        rate = 0.0
        id = 'out'

    return round(rate, 2), id


##############################################
def ReadXml(xmlfile ):
    value = xmlstru()
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
        boxstr.xmin = int( tmp.childNodes[0].nodeValue)

        tmp = obj.getElementsByTagName('ymin')[0]
        boxstr.ymin = int( tmp.childNodes[0].nodeValue)

        tmp = obj.getElementsByTagName('xmax')[0]
        boxstr.xmax = int( tmp.childNodes[0].nodeValue)

        tmp = obj.getElementsByTagName('ymax')[0]
        boxstr.ymax = int( tmp.childNodes[0].nodeValue)

        tmp = obj.getElementsByTagName('name')[0]
        boxstr.name = tmp.childNodes[0].nodeValue

        value.box.append(boxstr)

    return value

###########################################################################################
# read all images
READ_PATH = "/home/lishuang/Disk/shengshi_data/split/Train_data"
SAVE_PATH = "/home/lishuang/Disk/shengshi_data/split/Tk1_Train_data"

error_num=0
dirlen=len(os.listdir(READ_PATH))
num=0
file_data = ""
for dir in os.listdir(READ_PATH):
    FigDirectory = os.path.join(READ_PATH,dir,'JPEGImages')
    XmlDirectory = os.path.join(READ_PATH,dir,'Annotations')
    SaveFigDirectory = os.path.join(SAVE_PATH,dir,'JPEGImages')
    SaveXmlDirectory = os.path.join(SAVE_PATH,dir, 'Annotations')
    check_dir(SaveFigDirectory)
    check_dir(SaveXmlDirectory)
    roi_box = boxstru()
    roi_value = xmlstru()
    roi_box.xmin = 0
    roi_box.xmax = 640
    roi_box.ymin = 80
    roi_box.ymax = 400

    fig_names = loadAllTagFile(FigDirectory, '.jpg')

    num=num+1
    figlen=len(fig_names)
    for i in range(len(fig_names)):
        files = os.path.basename(fig_names[i])  # get file name
        filename = os.path.splitext(files)[0] #file's name
        # print(filename+'.jpg')
        print("[{}/{}]".format(num,dirlen),i+1,'/',figlen,' : ',filename + '.jpg')
        xmldir = os.path.join(XmlDirectory, filename + '.xml')# get absolute directory of relevant XML file's

        xml_name=(os.path.join(SaveXmlDirectory, os.path.splitext(fig_names[i].split('/')[-1])[0] + '.xml'))
        save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(fig_names[i].split('/')[-1])[0] + '.jpg'))
        fig = cv2.imread(fig_names[i])
        roi_image = fig[roi_box.ymin :roi_box.ymax,roi_box.xmin:roi_box.xmax]
        value = ReadXml(xmldir)  # read XML file from original directory
        result = []
        ######roi_box-[xmin,ymin,xmax,ymax]-[0,96,640,416]
        # print("len(bbox) = ", len(value.box))


        resulttmp=[]
        for ibox in range(len(value.box)):
            xmin = max(roi_box.xmin, value.box[ibox].xmin)
            ymin = max(roi_box.ymin, value.box[ibox].ymin)
            xmax = min(roi_box.xmax, value.box[ibox].xmax)
            ymax = min(roi_box.ymax, value.box[ibox].ymax)

            oriarea = (value.box[ibox].ymax - value.box[ibox].ymin) * (value.box[ibox].xmax - value.box[ibox].xmin)

            if ymax - ymin > 0 and xmax - xmin > 0 and 1.0 * (ymax - ymin) * (xmax - xmin) / oriarea > 0.45:
                xmin = xmin - roi_box.xmin
                xmax = xmax - roi_box.xmin
                ymin = ymin - roi_box.ymin
                ymax = ymax - roi_box.ymin

                label_name = '1'
                result.append([xmin, ymin, xmax, ymax, label_name])




            rate, id = annalysisOverlap(roi_box,value.box[ibox])
            # print("rate = ", rate, "id = ", id)
            if(id == 'in') :
                xmin_tmp = value.box[ibox].xmin - roi_box.xmin#-
                ymin_tmp = value.box[ibox].ymin - roi_box.ymin#y-96
                xmax_tmp = value.box[ibox].xmax - roi_box.xmin#-
                ymax_tmp = value.box[ibox].ymax - roi_box.ymin#y-96
            if(id == 'big') :
                xmin_tmp = value.box[ibox].xmin - roi_box.xmin#-
                ymin_tmp = roi_box.ymin - roi_box.ymin
                xmax_tmp = value.box[ibox].xmax - roi_box.xmin#-
                ymax_tmp = roi_box.ymax - roi_box.ymin
            if((id == 'up') & (rate > 0.45)):
                xmin_tmp = value.box[ibox].xmin - roi_box.xmin
                ymin_tmp = roi_box.ymin - roi_box.ymin
                xmax_tmp = value.box[ibox].xmax - roi_box.xmin
                ymax_tmp = value.box[ibox].ymax - roi_box.ymin
            if((id == 'down') & (rate > 0.45)):
                xmin_tmp = value.box[ibox].xmin - roi_box.xmin
                ymin_tmp = value.box[ibox].ymin - roi_box.ymin
                xmax_tmp = value.box[ibox].xmax - roi_box.xmin
                ymax_tmp = roi_box.ymax - roi_box.ymin
            if(id == 'out'):
                continue
            label_name_tmp = '1'
            resulttmp.append([xmin_tmp, ymin_tmp, xmax_tmp, ymax_tmp,label_name_tmp])


        if result != resulttmp:
            error_num=error_num+1
            file_data+=fig_names[i]+'\n'
            print('error_num=',error_num)
            
        if len(result)==0: #delete empty xml image
            continue
        cv2.imwrite(save_roiimage_path,roi_image)
        CreatXml(roi_image, result, xml_name)
        
print('final error_num=',error_num)
with open('Tk1_Train_data_comapre_errorxml.txt','w') as f:
        f.write(file_data)
