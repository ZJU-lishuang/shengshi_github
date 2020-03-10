import os
import cv2
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

    if len(root.findall('object')) ==1:
        return 1
    else:
        return 0
    

if __name__ == '__main__':

    READ_JSON_PATH = "/home/lishuang/Disk/shengshi_data/Follow_mask/gtFine/train"
    READ_IMG_PATH="/home/lishuang/Disk/shengshi_data/Follow_mask/img/train"
    SAVE_PATH = "/home/lishuang/Disk/shengshi_data/mask"

    file_data = ""
    dirlen=len(os.listdir(READ_JSON_PATH))
    num=0
    for dir in os.listdir(READ_JSON_PATH):
        FigDirectory = os.path.join(READ_IMG_PATH, dir)
        XmlDirectory = os.path.join(READ_JSON_PATH, dir)
        SaveFigDirectory = os.path.join(SAVE_PATH, dir,'JPEGImages')
        SaveXmlDirectory = os.path.join(SAVE_PATH, dir,'Annotations')
        check_dir(SaveFigDirectory)
        check_dir(SaveXmlDirectory)

        fig_names = loadAllTagFile(XmlDirectory, '.json')
        
        num=num+1
        figlen=len(fig_names)
        for i in range(len(fig_names)):
            file_path=fig_names[i]
            files = os.path.basename(fig_names[i])  # get file name
            filename = os.path.splitext(files)[0]  # file's name
            print("[{}/{}]".format(num,dirlen),i+1,'/',figlen,' : ',filename + '.json')
            xmldir = os.path.join(FigDirectory, filename + '.jpg')  # get absolute directory of relevant XML file's
            #move
            xml_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.json'))
            save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.jpg'))

            file_data+=os.path.splitext(file_path.split('/')[-1])[0]+'\n'

            shutil.copyfile(file_path,xml_name)
            shutil.copyfile(xmldir,save_roiimage_path)  
    with open('trainval.txt','w') as f:
        f.write(file_data)



    



