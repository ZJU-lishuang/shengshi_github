import os
import cv2
import shutil

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

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

def search(path,filename):
    path_file=[]
    for root,dirs,files in os.walk(path):
        if filename in dirs or filename in files:
            root=str(root)
            re_path=os.path.join(root,filename)
            path_file.append(re_path)
    
    return path_file

if __name__ == '__main__':

    DATA_PATH="/home/lishuang/Disk/dukto/防尾随关键点标注"
    READ_PATH = "/home/lishuang/Disk/shengshi_data/w32_512_adam_lr1e-3_04trainjson"
    SAVE_PATH="/home/lishuang/Disk/shengshi_data/new_13pointtestlist"
    file_data = ""
    
    data_dirs=[]
    for dir in os.listdir(DATA_PATH):
        data_dirs.append(dir)
    
    for dir in os.listdir(READ_PATH):
        if dir in data_dirs:
            FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
            JsonDirectory = os.path.join(READ_PATH, dir, 'json')

            SaveFigDirectory = os.path.join(SAVE_PATH, dir, 'JPEGImages')
            SaveJsonDirectory = os.path.join(SAVE_PATH, dir, 'Annotations')
            check_dir(SaveFigDirectory)
            check_dir(SaveJsonDirectory)


            fig_names = loadAllTagFile(FigDirectory, '.jpg')
            
            data_names=[]
            DataFigDirectory = os.path.join(DATA_PATH, dir)
            for root,dirs,files in os.walk(DataFigDirectory):
                for name in files:
                    if os.path.splitext(name)[1] == '.jpg':
                        data_names.append(name)

            for fig_name in fig_names:
                flag=0
                for data_name in data_names:
                    if data_name in fig_name:
                        flag=1
                        break
                if flag == 0:
                    files = os.path.basename(fig_name)  # get file name
                    filename = os.path.splitext(files)[0]  # file's name
                    save_image_path=os.path.join(SaveFigDirectory,filename + '.jpg')
                    jsonfile = os.path.join(JsonDirectory, filename + '.json') 
                    save_json_path = os.path.join(SaveJsonDirectory, filename + '.json')
                    shutil.copyfile(fig_name,save_image_path)  
                    shutil.copyfile(jsonfile,save_json_path)  
                    file_data+=fig_name+'\n'
        # else:
        #     shutil.copytree(os.path.join(READ_PATH, dir), os.path.join(SAVE_PATH, dir)) 


    with open('13keypoint_trainlist.txt','w') as f:
        f.write(file_data)



