import os
import json
import shutil

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

def checkjson(jsonfile):
    json_ann = json.load(open(jsonfile))
    objects_anns = json_ann['objects']
    flag=0
    # flag=1
    for objects_ann in objects_anns:
        headvision=objects_ann['keypoints'][2][2]
        # if headvision != 0:
        #     flag=0
        if headvision != 2:
            flag=1
            break
    
    return flag



if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/new_13pointtrainlist"
    SAVE_PATH = "/home/lishuang/Disk/shengshi_data/new_headpointtrainlist"

    file_data = ""
    dirlen=len(os.listdir(READ_PATH))
    num=0
    for dir in os.listdir(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        # JsonDirectory = os.path.join(READ_PATH, dir, dir)
        JsonDirectory = os.path.join(READ_PATH, dir, 'Annotations')
        if dir=="keypoint_lishuang":
            continue
        if dir=="keypoint_chenwei":
            continue
        if dir=="keypoint_wangweijian":
            continue
        if dir=="keypoint_wdd_json":
            continue

        SaveFigDirectory = os.path.join(SAVE_PATH, dir, 'JPEGImages')
        SaveXmlDirectory = os.path.join(SAVE_PATH, dir, 'Annotations')
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
            jsonfile = os.path.join(JsonDirectory, filename + '.json')  # get absolute directory of relevant XML file's
            #move
            xml_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.json'))
            save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.jpg'))

            if  not os.path.exists(jsonfile):
                continue

            checksign=checkjson(jsonfile)

            if checksign == 0 :
                shutil.copyfile(file_path,save_roiimage_path)  
                shutil.copyfile(jsonfile,xml_name)  



            # if checksign < 0 :
            #     # file_data.append(fig_names[i])
            #     file_data+=fig_names[i]+'\n'
            #     #move
            #     # shutil.move(file_path,save_roiimage_path)
            #     # shutil.move(xmldir,xml_name)    


    # with open('1021_cut_pic_errorxml.txt','w') as f:
    #     f.write(file_data)