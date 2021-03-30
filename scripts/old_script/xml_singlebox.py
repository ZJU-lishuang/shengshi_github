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


def get(root, name):
    vars = root.findall(name)
    return vars

def get_and_check(root, name, length):
    vars = root.findall(name)
    if len(vars) == 0:
        raise NotImplementedError('Can not find %s in %s.' % (name, root.tag))
    if length > 0 and len(vars) != length:
        raise NotImplementedError('The size of %s is supposed to be %d, but is %d.' % (name, length, len(vars)))
    if length == 1:
        vars = vars[0]
    return vars

def isoverlap(xmin1,ymin1,xmax1,ymax1,xmin2,ymin2,xmax2,ymax2):
    xmin=max(xmin1,xmin2)
    xmax=min(xmax1,xmax2)
    ymin=max(ymin1,ymin2)
    ymax=min(ymax1,ymax2)
    w=xmax-xmin
    h=ymax-ymin
    if w>0 and h>0:
        return 1
    else:
        return 0

def check_xml(imagename, xmlname):
    fig = cv2.imread(imagename)
    imgh, imgw = fig.shape[0:2]
    in_file = open(xmlname)
    tree = ET.parse(in_file)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    # assert (w == imgw and h == imgh)
    if len(root.findall('object'))==0:
        print("error: ",imagename," has no box")
        return -1

    flag=0
    if len(root.findall('object'))!=1:  #single complex
        tmpxmin=[]
        tmpymin=[]
        tmpxmax=[]
        tmpymax=[]
        
        for obj in get(root, 'object'):
            bndbox = get_and_check(obj, 'bndbox', 1)
            xmin = int(get_and_check(bndbox, 'xmin', 1).text)
            ymin = int(get_and_check(bndbox, 'ymin', 1).text)
            xmax = int(get_and_check(bndbox, 'xmax', 1).text)
            ymax = int(get_and_check(bndbox, 'ymax', 1).text)
            assert (xmax > xmin)
            assert (ymax > ymin)
            tmpxmin.append(xmin)
            tmpymin.append(ymin)
            tmpxmax.append(xmax)
            tmpymax.append(ymax)

        for i in range(len(tmpxmin)):
            for j in range(i+1,len(tmpxmin)):
                flag=isoverlap(tmpxmin[i],tmpymin[i],tmpxmax[i],tmpymax[i],tmpxmin[j],tmpymin[j],tmpxmax[j],tmpymax[j])
                if flag == 1:
                    break
            if flag == 1:
                break

    return flag

    if len(root.findall('object')) ==1:
        return 1
    else:
        return 0
    

if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/test/Tk1_model_test_res48_output_LINEAR_single/sample1_1_gangzhuao"
    SAVE_PATH = "/home/lishuang/Disk/test/Tk1_model_test_res48_output_LINEAR_single/error"

    file_data = ""
    dirlen=len(os.listdir(READ_PATH))
    num=0
    for dir in os.listdir(READ_PATH):
        # FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        # XmlDirectory = os.path.join(READ_PATH, dir, 'Annotations')
        # SaveFigDirectory = os.path.join(SAVE_PATH, dir, 'JPEGImages')
        # SaveXmlDirectory = os.path.join(SAVE_PATH, dir, 'Annotations')

        FigDirectory = os.path.join(READ_PATH, dir)
        XmlDirectory = os.path.join(READ_PATH, dir)
        SaveFigDirectory = os.path.join(SAVE_PATH, dir)
        SaveXmlDirectory = os.path.join(SAVE_PATH, dir)
        check_dir(SaveFigDirectory)
        check_dir(SaveXmlDirectory)

        fig_names = loadAllTagFile(FigDirectory, '.jpg')
        
        num=num+1
        figlen=len(fig_names)
        for i in range(len(fig_names)):
            file_path=fig_names[i]
            files = os.path.basename(fig_names[i])  # get file name
            filename = os.path.splitext(files)[0]  # file's name
            print("[{}/{}]".format(num,dirlen),i+1,'/',figlen,' : ',filename + '.jpg')
            xmldir = os.path.join(XmlDirectory, filename + '.xml')  # get absolute directory of relevant XML file's

            txtdir = os.path.join(XmlDirectory, filename + '.txt')  # get absolute directory of relevant XML file's
            #move
            xml_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.xml'))
            save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.jpg'))

            txt_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.txt'))


            checksign=check_xml(fig_names[i], xmldir)

            if checksign==1:
                #move
                shutil.move(file_path,save_roiimage_path)
                shutil.move(xmldir,xml_name)  
                shutil.move(txtdir,txt_name)  



    



