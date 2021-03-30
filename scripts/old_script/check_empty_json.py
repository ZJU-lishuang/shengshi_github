import os
import json
import shutil


def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def search(path,filename):
    path_file=[]
    for root,dirs,files in os.walk(path):
        if filename in dirs or filename in files:
            root=str(root)
            re_path=os.path.join(root,filename)
            path_file.append(re_path)
    
    return path_file

def checkjson(jsonfile):
    json_ann = json.load(open(jsonfile))
    objects_anns = json_ann['objects']
    flag=0
    if len(objects_anns) > 0:
        flag=1    
    return flag

if __name__ == '__main__':
    DATA_PATH="/home/lishuang/Disk/shengshi_data/new_13pointtestlist"

    SAVE_PATH="/home/lishuang/Disk/shengshi_data/new_13pointtrainlistcheck"

    for dir in os.listdir(DATA_PATH):
        DataDirectory = os.path.join(DATA_PATH, dir)
        json_names=[]
        for root,dirs,files in os.walk(DataDirectory):
            for name in files:
                if os.path.splitext(name)[1] == '.json':
                    json_path=os.path.join(root,name)
                    if checkjson(json_path)  > 0:
                        json_names.append(json_path)
        

        SaveFigDirectory = os.path.join(SAVE_PATH, dir, 'JPEGImages')
        SaveJsonDirectory = os.path.join(SAVE_PATH, dir, 'Annotations')
        check_dir(SaveFigDirectory)
        check_dir(SaveJsonDirectory)
        for jsonfile in json_names:
            files=os.path.basename(jsonfile)
            filename = os.path.splitext(files)[0]  # file's name
            img_path=search(DataDirectory,filename + '.jpg')
            assert len(img_path)==1
            save_image_path=os.path.join(SaveFigDirectory,filename + '.jpg')
            save_json_path = os.path.join(SaveJsonDirectory, filename + '.json')
            shutil.copyfile(img_path[0],save_image_path)  
            shutil.copyfile(jsonfile,save_json_path)  
