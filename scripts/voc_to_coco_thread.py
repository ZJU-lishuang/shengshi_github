# coding=utf-8
import cv2
import os
import time
import json
import xml.etree.ElementTree as ET

from multiprocessing import Pool

PRE_DEFINE_CATEGORIES = {"1": 1}
START_BOUNDING_BOX_ID = 1


def get(root, name):
    vars = root.findall(name)
    return vars

def subdirs(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir():
            yield entry.name

def subfiles(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and not entry.is_dir():
            yield entry.name

###############loadAllTagFile##############
def loadAllTagFile( DirectoryPath, tag ):# download all files' name
    result = []
    for file in subfiles(DirectoryPath):
    # for file in os.listdir(DirectoryPath):
        file_path = os.path.join(DirectoryPath, file)
        if os.path.splitext(file_path)[1] == tag:
            result.append(file_path)
    return result

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


def convert(fig_names_all, xmldirs_all, fig_save):
    # json_dict = {"images":[], "type": "instances", "annotations": [],   #ls
    #             "categories": []}   #ls
    # json_dict = {"images": [], "annotations": [],  # ls
    #              "categories": []}  # ls

    imagestmp=[]
    annotationstmp=[]
    categories = PRE_DEFINE_CATEGORIES
    bnd_id = 1
    num = 0
    for i in range(len(fig_names_all)):
        xml_f = xmldirs_all[i]
        figname = fig_names_all[i]
        files = os.path.basename(figname)

        # print(os.path.basename(fig_names_all[0]),"start xml_f=",xml_f)
        tree = ET.parse(xml_f)
        # print(os.path.basename(fig_names_all[0]),"end xml_f=",xml_f)

        root = tree.getroot()

        if len(root.findall('object'))==0:
            continue

        # if len(root.findall('object'))!=1:  #single simple
        #     continue
    
        if len(root.findall('object'))!=1:  #single complex
            tmpxmin=[]
            tmpymin=[]
            tmpxmax=[]
            tmpymax=[]
            flag=0
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
            if flag==1:
                continue

        #时间主要消耗在保存图片
        fig = cv2.imread(figname)
        cv2.imwrite(os.path.join(fig_save, files), fig)

        ## The filename must be a number
        # filename = line[:-4]
        # image_id = get_filename_as_int(filename)  #ls
        num += 1
        if num % 50 == 0:
            print("PID:",os.getpid()," processing ", num)
        image_id = num  # ls

        size = get_and_check(root, 'size', 1)
        width = int(get_and_check(size, 'width', 1).text)
        height = int(get_and_check(size, 'height', 1).text)
        # image = {'file_name': filename, 'height': height, 'width': width,
        #          'id':image_id}
        image = {'file_name': files, 'height': height, 'width': width,
                 'id': image_id}
        imagestmp.append(image)
        ## Cruuently we do not support segmentation
        #  segmented = get_and_check(root, 'segmented', 1).text
        #  assert segmented == '0'
        # continue  #ls
        for obj in get(root, 'object'):
            category = get_and_check(obj, 'name', 1).text
            if category not in categories:
                print("error category image:",figname)
                # new_id = len(categories)
                # categories[category] = new_id
            category_id = categories[category]
            bndbox = get_and_check(obj, 'bndbox', 1)
            xmin = int(get_and_check(bndbox, 'xmin', 1).text)
            ymin = int(get_and_check(bndbox, 'ymin', 1).text)
            xmax = int(get_and_check(bndbox, 'xmax', 1).text)
            ymax = int(get_and_check(bndbox, 'ymax', 1).text)
            assert (xmax > xmin)
            assert (ymax > ymin)
            o_width = abs(xmax - xmin)
            o_height = abs(ymax - ymin)
            ann = {'iscrowd': 0, 'file_name': files,'image_id':
                image_id, 'bbox': [xmin, ymin, o_width, o_height],
                   'category_id': category_id, 'id': bnd_id, 'ignore': 0}
            annotationstmp.append(ann)
            bnd_id = bnd_id + 1

    return imagestmp,annotationstmp



def convert_thread(arglist):
    fig_names_all, xmldirs_all, fig_save=arglist
    return convert(fig_names_all, xmldirs_all, fig_save)

def convert_singleprocess(fig_names_all, xmldirs_all, fig_save,json_file):
    # json_dict = {"images":[], "type": "instances", "annotations": [],   #ls
    #             "categories": []}   #ls
    json_dict = {"images": [], "annotations": [],  # ls
                 "categories": []}  # ls
    categories = PRE_DEFINE_CATEGORIES
    bnd_id = START_BOUNDING_BOX_ID
    num = 0
    for i in range(len(fig_names_all)):
        xml_f = xmldirs_all[i]
        figname = fig_names_all[i]
        files = os.path.basename(figname)
        # print("xml_f=",xml_f)
        tree = ET.parse(xml_f)
        root = tree.getroot()

        if len(root.findall('object'))==0:
            continue

        if num == 10000:
            break

        if len(root.findall('object'))!=1:  #single complex
            tmpxmin=[]
            tmpymin=[]
            tmpxmax=[]
            tmpymax=[]
            flag=0
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
            if flag==1:
                continue

        #时间主要消耗在保存图片
        fig = cv2.imread(figname)
        cv2.imwrite(os.path.join(fig_save, files), fig)

        ## The filename must be a number
        # filename = line[:-4]
        # image_id = get_filename_as_int(filename)  #ls
        num += 1
        if num%50==0:
            print("processing ",num)
        
        
        image_id = num  # ls
        size = get_and_check(root, 'size', 1)
        width = int(get_and_check(size, 'width', 1).text)
        height = int(get_and_check(size, 'height', 1).text)
        # image = {'file_name': filename, 'height': height, 'width': width,
        #          'id':image_id}
        image = {'file_name': files, 'height': height, 'width': width,
                 'id': image_id}
        json_dict['images'].append(image)
        ## Cruuently we do not support segmentation
        #  segmented = get_and_check(root, 'segmented', 1).text
        #  assert segmented == '0'
        # continue  #ls
        for obj in get(root, 'object'):
            category = get_and_check(obj, 'name', 1).text
            if category not in categories:
                print("error category image:",figname)
                # new_id = len(categories)
                # categories[category] = new_id
            category_id = categories[category]
            bndbox = get_and_check(obj, 'bndbox', 1)
            xmin = int(get_and_check(bndbox, 'xmin', 1).text)
            ymin = int(get_and_check(bndbox, 'ymin', 1).text)
            xmax = int(get_and_check(bndbox, 'xmax', 1).text)
            ymax = int(get_and_check(bndbox, 'ymax', 1).text)
            assert (xmax > xmin)
            assert (ymax > ymin)
            o_width = abs(xmax - xmin)
            o_height = abs(ymax - ymin)
            ann = {'iscrowd': 0, 'image_id':
                image_id, 'bbox': [xmin, ymin, o_width, o_height],
                   'category_id': category_id, 'id': bnd_id, 'ignore': 0}
            json_dict['annotations'].append(ann)
            bnd_id = bnd_id + 1

    for cate, cid in categories.items():
        cat = {'supercategory': 'none', 'id': cid, 'name': cate}
        json_dict['categories'].append(cat)
    json_fp = open(json_file, 'w')
    json_str = json.dumps(json_dict)
    json_fp.write(json_str)
    json_fp.close()


if __name__ == '__main__':

    READ_PATH = "/home/lishuang/Disk/shengshi_data/xilixiang"
    json_file = "/home/lishuang/Disk/shengshi_data/xilixiang_coco/annotations/pascal_trainval0712.json"
    fig_save="/home/lishuang/Disk/shengshi_data/xilixiang_coco/images"

    fig_names_all = []
    xmldirs_all = []
    xml_names_all = []
    save_roiimage_paths_all = []
    starttime = time.time()
    for dir in subdirs(READ_PATH):
        FigDirectory = os.path.join(READ_PATH, dir, 'JPEGImages')
        XmlDirectory = os.path.join(READ_PATH, dir, 'Annotations')

        fig_names = []
        xmldirs = []
        tag = '.jpg'
        for file in subfiles(FigDirectory):
            # for file in os.listdir(DirectoryPath):
            file_path = os.path.join(FigDirectory, file)
            if os.path.splitext(file_path)[1] == tag:
                fig_names.append(file_path)

                files = os.path.basename(file_path)  # get file name
                filename = os.path.splitext(files)[0]  # file's name
                xmldir = os.path.join(XmlDirectory, filename + '.xml')
                xmldirs.append(xmldir)

        fig_names_all.extend(fig_names)
        xmldirs_all.extend(xmldirs)

    print("time=", time.time() - starttime)

    # convert_singleprocess(fig_names_all, xmldirs_all, fig_save,json_file)  #singleprocess

    #多进程读写文件（I/O密集型），瓶颈在磁盘寻址速度上，和单进程读写文件速度相差不大

    # starttime = time.time()
    # cpu_num_process=6
    # num_process = 512
    # avg = int(len(fig_names_all) / num_process)
    # late = len(fig_names_all) % num_process
    # p = Pool(cpu_num_process)
    # res_l = []
    # for i in range(num_process):
    #     start = i * avg
    #     if i == num_process - 1:
    #         end = (i + 1) * avg + late
    #     else:
    #         end = (i + 1) * avg
    #     fig_names_all_now = fig_names_all[start:end]
    #     xmldirs_all_now = xmldirs_all[start:end]
    #     arglist = [fig_names_all_now, xmldirs_all_now,fig_save]
    #     result = p.apply_async(convert_thread, args=(arglist,))
    #     res_l.append(result)
    # p.close()
    # p.join()

    # print("process time=", time.time() - starttime)
    
    # images_all=[]
    # annotations_all=[]
    # for res in res_l:
    #     images, annotations =res.get()
    #     images_all.extend(images)
    #     annotations_all.extend(annotations)

    # imagename={}
    # print("image num = ",len(images_all))
    # starttime = time.time()
    # for i in range(len(images_all)):
    #     images_all[i]['id']=i+1
    #     imagename[images_all[i]['file_name']]=images_all[i]['id']

    # print("images_all time=", time.time() - starttime)

    # starttime = time.time()
    # for i in range(len(annotations_all)):
    #     annotations_all[i]['image_id']=imagename[annotations_all[i]['file_name']]
    #     annotations_all[i]['id']=i+1
    #     del annotations_all[i]['file_name']

    # print("annotations_all time=", time.time() - starttime)


    # json_dict = {"images": [], "annotations": [],  # ls
    #              "categories": []}  # ls

    # json_dict['annotations']=annotations_all
    # json_dict['images'] = images_all
    # categories = PRE_DEFINE_CATEGORIES
    # for cate, cid in categories.items():
    #     cat = {'supercategory': 'none', 'id': cid, 'name': cate}
    #     json_dict['categories'].append(cat)
    # json_fp = open(json_file, 'w')
    # json_str = json.dumps(json_dict)
    # json_fp.write(json_str)
    # json_fp.close()

    # print("end")

    # json_file = "/home/lishuang/Disk/shengshi_data/split/dataset_Tk1_beijing_single/voc/annotations/pascal_trainval0712.json"
    # fig_save="/home/lishuang/Disk/shengshi_data/split/dataset_Tk1_beijing_single/voc/images"
    # json_file = "/home/lishuang/Disk/shengshi_data/split/Tk1_Train_data_single/voc/annotations/pascal_trainval0712.json"
    # fig_save="/home/lishuang/Disk/shengshi_data/split/Tk1_Train_data_single/voc/images"

    starttime = time.time()
    convert_singleprocess(fig_names_all, xmldirs_all, fig_save,json_file)  #singleprocess
    print("single process time=", time.time() - starttime)

