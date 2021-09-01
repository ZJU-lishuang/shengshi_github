import os
import xml.etree.ElementTree as ET
import numpy as np
import mmcv
import shutil
# import re

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

def checkdir(dirpath):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)

def GetFileFromThisRootDir(dir,ext = None):
  allfiles = []
  needExtFilter = (ext != None)
  for root,dirs,files in os.walk(dir):
    for filespath in files:
      filepath = os.path.join(root, filespath)
      extension = os.path.splitext(filepath)[1]
      if needExtFilter and extension in ext:
        allfiles.append(filepath)
      elif not needExtFilter:
        allfiles.append(filepath)
  return allfiles

def gen_dataset():
    # dataset_xml = '/home/lishuang/Disk/gitlab/traincode/video_action_det/data/ava_xianchang/天府机场标签'
    dataset_xml='/home/lishuang/Disk/dukto/异常行为标注/action_train'
    # dataset_xml='/home/lishuang/Disk/dukto/异常行为标注/action_val'
    xml_names = GetFileFromThisRootDir(dataset_xml, '.xml')
    xml_names.sort()

    total_ann = {}
    total_entity_id = []
    total_action_labels = []
    total_action_labels_num = {}
    for xml_path in xml_names:
        img_basename = os.path.basename(xml_path)
        tree = ET.parse(xml_path)
        root = tree.getroot()
        size = root.find('imagesize')
        w = int(size.find('ncols').text)
        h = int(size.find('nrows').text)
        video_id, frame_id = os.path.splitext(img_basename)[0].rsplit('_', 1)
        if video_id == 'frame':
            video_id=os.path.basename(os.path.dirname(xml_path))
            if video_id =="default":
                video_id = os.path.basename(os.path.dirname(os.path.dirname(xml_path)))
        if video_id not in total_ann:
            total_ann[video_id]={}

        timestamp = int(frame_id)

        for obj in root.findall('object'):
            name = obj.find('name').text
            if name != '异常行为人' and name != '正常行为人':
                continue
            labels = obj.find('attributes').text

            for label in labels.split(','):
                if '人物ID' in label:
                    entity_id = label
                if '异常行为' in label:
                    action_label = label
            if name == "正常行为人":
                action_label = "异常行为=正常"
                for label in labels.split(','):
                    if 'track_id' in label:
                        entity_id = video_id + '_' + label

            polygon = obj.find('polygon')
            pts = polygon.findall('pt')
            bbox = [
                float(pts[0].find('x').text) ,
                float(pts[0].find('y').text) ,
                float(pts[2].find('x').text) ,
                float(pts[2].find('y').text)
            ]
            action_label = action_label.strip()
            entity_id = entity_id.strip()
            if entity_id not in total_ann[video_id]:
                total_ann[video_id][entity_id] = {}
            if action_label not in total_ann[video_id][entity_id]:
                total_ann[video_id][entity_id][action_label] = {}
            if timestamp not in total_ann[video_id][entity_id][action_label]:
                total_ann[video_id][entity_id][action_label][timestamp] = {}

            total_ann[video_id][entity_id][action_label][timestamp]['bbox'] = bbox

            if action_label not in total_action_labels:
                total_action_labels.append(action_label)

    def custom_action_labels():
        return [
            '异常行为=头撞墙', '异常行为=砸门', '异常行为=正常', '异常行为=扇巴掌', '异常行为=掐脖子', '异常行为=举高', '异常行为=撞桌', '异常行为=打斗',
            '异常行为=打滚', '异常行为=快速移动', '异常行为=举标语', '异常行为=发传单'
        ]

    # dst_dir_path="./result_csv"
    
    #25帧为1秒，1分钟1500帧
    for video_name,total_ids in total_ann.items():
        file_data = "action_name,video_name,frame_start,frame_end,xmin,ymin,xmax,ymax\n"
        #单个视频
        for entity_id,actions in total_ids.items():
            #单个跟踪目标
            for action_name,total_frame in actions.items():
                #单个行为动作时
                frame_start=-1
                frame_end=-1
                person_box_list=[]
                for frame_id,person_ann in total_frame.items():
                    #update start frame at beginning
                    if frame_start < 0:
                        frame_start=frame_id
                    person_box_list.append(person_ann['bbox'])
                    frame_end = frame_id
                    #当记录开始帧位置，且帧数长度在一定范围内，不长也不短，记录结束帧位置，重置参数准备下一次记录
                    #150 6s  300 12s
                    if frame_start >= 0 and frame_end-frame_start >=150 and frame_end-frame_start <=300:
                        xmin=np.array(person_box_list)[:,0].min()
                        ymin=np.array(person_box_list)[:,1].min()
                        xmax = np.array(person_box_list)[:, 2].max()
                        ymax = np.array(person_box_list)[:, 3].max()
                        # person_region=[xmin,ymin,xmax,ymax]
                        #知道action_name，video_name,frame_start，frame_end,person_region
                        file_data+=f"{action_name},{video_name},{frame_start},{frame_end},{xmin},{ymin},{xmax},{ymax}\n"
                        #update start position for next action video
                        frame_start=frame_end
                        person_box_list=[]
                    #存在开始帧位置，但中间中断后又重新找回,导致时间过长，放弃截取
                    elif frame_start >= 0 and frame_end-frame_start >=300:
                        frame_start=frame_end
                        person_box_list=[]
                #末尾有较短但合适的视频
                if frame_end-frame_start >=75:
                    xmin = np.array(person_box_list)[:, 0].min()
                    ymin = np.array(person_box_list)[:, 1].min()
                    xmax = np.array(person_box_list)[:, 2].max()
                    ymax = np.array(person_box_list)[:, 3].max()
                    file_data += f"{action_name},{video_name},{frame_start},{frame_end},{xmin},{ymin},{xmax},{ymax}\n"

        with open(f"result_csv/result_{video_name}.txt",'w') as f:
            f.write(file_data)
        # break


if __name__ == '__main__':
    gen_dataset()