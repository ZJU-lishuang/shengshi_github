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

def instance_json(json_path,new_path):
    with open(json_path) as f1:
        json_ann = json.load(f1)
        person=0
        baby=0
        for shape in json_ann['objects']:
            label = shape['label']
            if label=='person' or label =='1':
                person=person+1
                shape['label']='person'+'-'+str(person)
            elif label=='baby':
                baby=baby+1
                shape['label']='baby'+'-'+str(baby)

        with open(new_path,'w') as f2:
            json.dump(json_ann,f2,sort_keys=True,indent=4) 
            # json.dump(json_ann,f2, ensure_ascii=True, indent=2)
    
    # for shape in json_ann['objects']:
    #     if person>1 or baby >1:
    #         label = shape['label']
    #         if label=='person':
    #             shape['label']='person'+'-'+str(person)
    #             person=person-1
    #         elif label=='baby':
    #             shape['label']='baby'+'-'+str(baby)
    #             baby=baby-1
    #     else:
    #         break


if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/mask"
    SAVE_PATH = "/home/lishuang/Disk/shengshi_data/mask_single"

    file_data = ""
    dirlen=len(os.listdir(READ_PATH))
    num=0
    for dir in os.listdir(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir,'JPEGImages')
        XmlDirectory = os.path.join(READ_PATH, dir,'Annotations')
        SaveFigDirectory = os.path.join(SAVE_PATH, dir,'JPEGImages')
        SaveXmlDirectory = os.path.join(SAVE_PATH, dir,'Annotations')
        # SaveFigDirectory = os.path.join(SAVE_PATH,'json2coco')  #labelme2coco
        # SaveXmlDirectory = os.path.join(SAVE_PATH,'json2coco')
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
            xmldir = os.path.join(XmlDirectory, filename + '.json')  # get absolute directory of relevant XML file's
            #move
            xml_name = (os.path.join(SaveXmlDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.json'))
            save_roiimage_path = (os.path.join(SaveFigDirectory, os.path.splitext(file_path.split('/')[-1])[0] + '.jpg'))

            file_data+=os.path.splitext(file_path.split('/')[-1])[0]+'\n'


            instance_json(xmldir,xml_name)
            shutil.copyfile(file_path,save_roiimage_path)  

    with open('trainval.txt','w') as f:
        f.write(file_data)