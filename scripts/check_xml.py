import os
import cv2
import xml.etree.ElementTree as ET

def loadAllTagFile( DirectoryPath, tag ):# download all files' name
    result = []
    for file in os.listdir(DirectoryPath):
        file_path = os.path.join(DirectoryPath, file)
        if os.path.splitext(file_path)[1] == tag:
            result.append(file_path)
    return result


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
    for obj in root.findall('object'):
        cls = obj.find('name').text

        xmlbox = obj.find('bndbox')
        xmin = xmlbox.find('xmin').text
        xmax = xmlbox.find('xmax').text
        ymin = xmlbox.find('ymin').text
        ymax = xmlbox.find('ymax').text

        xmin = int(xmin)
        xmax = int(xmax)
        ymin = int(ymin)
        ymax = int(ymax)

        # assert (xmin >= 0 and xmin < w)
        # assert (xmax > xmin and xmax <= w)
        #
        # assert (ymin >= 0 and ymin < h)
        # assert (ymax > ymin and ymax <= h)
        if  not ((xmin >= 0 and xmin < w) and (xmax > xmin and xmax <= w) and (ymin >= 0 and ymin < h) and (ymax > ymin and ymax <= h)):
            return -1

    return 0

if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/split/Tk1_Train_data"

    file_data = ""
    for dir in os.listdir(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        XmlDirectory = os.path.join(READ_PATH, dir, 'Annotations')

        fig_names = loadAllTagFile(FigDirectory, '.jpg')


        for i in range(len(fig_names)):
            files = os.path.basename(fig_names[i])  # get file name
            filename = os.path.splitext(files)[0]  # file's name
            print(filename + '.jpg')
            xmldir = os.path.join(XmlDirectory, filename + '.xml')  # get absolute directory of relevant XML file's


            checksign=check_xml(fig_names[i], xmldir)

            if checksign < 0 :
                # file_data.append(fig_names[i])
                file_data+=fig_names[i]+'\n'


    with open('errorxml.txt','w') as f:
        f.write(file_data)



