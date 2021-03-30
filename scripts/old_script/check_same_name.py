import os
import cv2
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


if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/新建文件夹/home/lzm/Disk3T/Train_data/Datasets/TX2/Jpg/1021_cut_pic"

    file_data = ""

    fig_names_all = []
    for dir in os.listdir(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        XmlDirectory = os.path.join(READ_PATH, dir, 'Annotations')

        fig_names = loadAllTagFile(FigDirectory, '.jpg')
        
        fig_names_all.extend(fig_names)
    
    for i in range(len(fig_names_all)):
        filebasenameA=os.path.basename(fig_names_all[i])
        filenum=0
        filesamename=""
        print(" process :",i+1,"/",len(fig_names_all))
        for j in range(i+1,len(fig_names_all)):
            filebasenameB=os.path.basename(fig_names_all[j])
            if filebasenameA==filebasenameB and i!=j:
                filenum=filenum+1
                filesamename+=fig_names_all[j]+'\n'
        
        if filenum > 0:
            print(fig_names_all[i]+" has same image name")
            file_data+=fig_names_all[i]+'\n'+'the same with '+filesamename


    with open('1021_cut_pic_samefile.txt','w') as f:
        f.write(file_data)



