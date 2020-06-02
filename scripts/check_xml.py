import os
import cv2
import math
import shutil
import xml.etree.ElementTree as ET

def subfiles(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and not entry.is_dir():
            yield entry.name

def loadAllTagFile( DirectoryPath, tag ):# download all files' name
    result = []
    for file in subfiles(DirectoryPath):
    # for file in os.listdir(DirectoryPath):
        file_path = os.path.join(DirectoryPath, file)
        if os.path.splitext(file_path)[1] == tag:
            result.append(file_path)
    return result


def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def check_xml(imagename, xmlname):
    fig = cv2.imread(imagename)
    imgh, imgw = fig.shape[0:2]
    in_file = open(xmlname)
    tree = ET.parse(in_file)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    assert (w == imgw and h == imgh)
    if len(root.findall('object'))==0:
        print("error: ",imagename," has no box")
        return -1
    centerx=[]
    centery=[]
    for obj in root.findall('object'):
        cls_name = obj.find('name').text

        xmlbox = obj.find('bndbox')
        xmin = xmlbox.find('xmin').text
        xmax = xmlbox.find('xmax').text
        ymin = xmlbox.find('ymin').text
        ymax = xmlbox.find('ymax').text

        xmin = int(xmin)
        xmax = int(xmax)
        ymin = int(ymin)
        ymax = int(ymax)
        cls_num=int(cls_name)

        if cls_num!=1:
            return -1


        centerx.append((xmax-xmin)/2)
        centery.append((ymax-ymin)/2)

        # assert (xmin >= 0 and xmin < w)
        # assert (xmax > xmin and xmax <= w)
        #
        # assert (ymin >= 0 and ymin < h)
        # assert (ymax > ymin and ymax <= h)
        if  not ((xmin >= 0 and xmin < w) and (xmax > xmin and xmax <= w) and (ymin >= 0 and ymin < h) and (ymax > ymin and ymax <= h)):
            print("error: ",imagename," out of image")
            return -1
        if  (xmax-xmin)*(ymax-ymin)<10 or (xmax-xmin) <10 or (ymax-ymin)<10:
            print("error: ",imagename," has error boxes")
            return -1

    objnum=len(root.findall('object'))
    distance=10000
    if objnum > 1:
        for i in range(objnum):
            centerx1=centerx[i]
            centery1=centery[i]
            for j in range(i+1,objnum):
                centerx2=centerx[j]
                centery2=centery[j]
                distancetmp=math.sqrt((centery2-centery1)**2+(centerx2-centerx1)**2)
                if distancetmp < distance:
                    distance=distancetmp
    
    return distance

if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/机场行李箱数据"
    # SAVE_PATH = "/home/lishuang/Disk/shengshi_data/split/Tk1_Train_data"

    file_data = ""
    dirlen=len(os.listdir(READ_PATH))
    num=0
    distance=10000
    for dir in os.listdir(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        XmlDirectory = os.path.join(READ_PATH, dir, 'Annotations')
        # SaveFigDirectory = os.path.join(SAVE_PATH, dir, 'JPEGImages')
        # SaveXmlDirectory = os.path.join(SAVE_PATH, dir, 'Annotations')
        # check_dir(SaveFigDirectory)
        # check_dir(SaveXmlDirectory)

        fig_names = loadAllTagFile(FigDirectory, '.jpg')
        
        num=num+1
        figlen=len(fig_names)
        for i in range(len(fig_names)):
            file_path=fig_names[i]
            files = os.path.basename(fig_names[i])  # get file name
            filename = os.path.splitext(files)[0]  # file's name
            print("[{}/{}]".format(num,dirlen),i+1,'/',figlen,' : ',filename + '.jpg')
            xmldir = os.path.join(XmlDirectory, filename + '.xml')  # get absolute directory of relevant XML file's
            #move
            # xml_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.xml'))
            # save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.jpg'))


            checksign=check_xml(fig_names[i], xmldir)

            if checksign>0 and distance > checksign:
                distance=checksign
            print("min distance=",distance)

            if checksign < 0 :
                # file_data.append(fig_names[i])
                file_data+=fig_names[i]+'\n'
                #move
                # shutil.move(file_path,save_roiimage_path)
                # shutil.move(xmldir,xml_name)    


    with open('1021_cut_pic_errorxml.txt','w') as f:
        f.write(file_data)
        f.write(str(distance))



