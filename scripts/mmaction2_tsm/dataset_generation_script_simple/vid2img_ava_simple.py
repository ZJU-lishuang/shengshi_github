# Code for "TSM: Temporal Shift Module for Efficient Video Understanding"
# arXiv:1811.08383
# Ji Lin*, Chuang Gan, Song Han
# {jilin, songhan}@mit.edu, ganchuang@csail.mit.edu

from __future__ import print_function, division
import os
import sys
import subprocess
from multiprocessing import Pool
from tqdm import tqdm
import numpy as np

import cv2


n_thread = 48

def read_labelmap(labelmap_file):
    """Reads a labelmap without the dependency on protocol buffers.

    Args:
        labelmap_file: A file object containing a label map protocol buffer.

    Returns:
        labelmap: The label map in the form used by the
        object_detection_evaluation
        module - a list of {"id": integer, "name": classname } dicts.
        class_ids: A set containing all of the valid class id integers.
    """
    labelmap = []
    class_ids = set()
    name = ''
    class_id = ''
    for line in labelmap_file:
        if line.startswith('  name:'):
            name = line.split('"')[1]
        elif line.startswith('  id:') or line.startswith('  label_id:'):
            class_id = int(line.strip().split(' ')[-1])
            labelmap.append({'id': class_id, 'name': name})
            class_ids.add(class_id)
    return labelmap, class_ids

def vid2shortvid(video_path,out_name,frame_start, frame_end, xmin,ymin,xmax,ymax):
    if '.mp4' not in video_path:
        return

    cap = cv2.VideoCapture(video_path)  # 打开视频文件
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # 获得视频文件的帧数
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获得视频文件的帧率
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # 获得视频文件的帧宽
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # 获得视频文件的帧高

    # 创建保存视频文件类对象
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # fourcc = cv2.VideoWriter_fourcc(*'H264')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    cut_width=xmax-xmin
    cut_height=ymax-ymin
    
    ratio_big=0.5
    ratio_small=0.25
    ratio_ww=1
    ratio_hh=1
    if cut_width/width>0.25:
        ratio_ww=0.5
    if cut_height/height>0.25:
        ratio_hh=0.5

    if cut_width > cut_height:
        ratio_w=ratio_small*ratio_ww
        ratio_h=ratio_big*ratio_hh
    else:
        ratio_w=ratio_big*ratio_ww
        ratio_h=ratio_small*ratio_hh
   
    xmin=xmin-cut_width*ratio_w
    xmax=xmax+cut_width*ratio_w
    new_width=(2*ratio_w+1)*cut_width
    if new_width>width-1:
        new_width=width-1
    if xmin < 0:
        xmin=0
        xmax=xmin+new_width
    if xmax > width-1:
        xmax=width-1
        xmin=xmax-new_width
    ymin=ymin-cut_height*ratio_h
    ymax=ymax+cut_height*ratio_h
    new_height=(2*ratio_h+1)*cut_height
    if new_height>height-1:
        new_height=height-1
    if ymin < 0:
        ymin=0
        ymax=ymin+new_height
    if ymax > height-1:
        ymax=height-1
        ymin=ymax-new_height
    # xmin=max(xmin-cut_width*2,0)
    # xmax=min(xmax+cut_width*2,width)
    # ymin=max(ymin-cut_height,0)
    # ymax=min(ymax+cut_height,height)
    xmax=int(xmax)
    xmin=int(xmin)
    ymax=int(ymax)
    ymin=int(ymin)
    cut_width=xmax-xmin
    cut_height=ymax-ymin
    out = cv2.VideoWriter(out_name, fourcc, fps, (int(cut_width), int(cut_height)))

    # 计算视频长度/s
    video_length = frames / fps
#     print('start and stop must < %.1f' % video_length)  # 提示输入变量的范围
    start = frame_start/fps
#     print("start time/s: {}".format(start))
    frame_end=min(frames-1,frame_end)
    stop = frame_end/fps
#     print("stop time/s: {}".format(stop))
    # 设置帧读取的开始位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, start * fps)
    pos = cap.get(cv2.CAP_PROP_POS_FRAMES)  # 获得帧位置
#     video_empty=True
    while (pos <= stop * fps):
        ret, frame = cap.read()  # 捕获一帧图像
        frame=frame[int(ymin):int(ymax),int(xmin):int(xmax)]
        try:
            out.write(frame)
        except:
            continue
        pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
#         if video_empty:
#             video_empty=False

    cap.release()
    out.release()
#     if video_empty:
#         print("{} is empty".format(out_name))
#         os.remove(out_name)

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

def line_mul(line_id,vid_name_dic):
    line,person_id=line_id
    line = line.rstrip()
    items = line.split(',')
    video_path = vid_name_dic[items[1]]
    label_name = items[0]

    class_name = label_name.replace("异常行为=", "")
    dst_class_path = os.path.join(dst_dir_path, class_name)
    checkdir(dst_class_path)

    out_name = os.path.join(dst_class_path, f"{items[1]}_{person_id}.mp4")
    frame_start = int(items[2])
    frame_end = int(items[3])

    xmin = int(float(items[4]))
    ymin = int(float(items[5]))
    xmax = int(float(items[6]))
    ymax = int(float(items[7]))

    vid2shortvid(video_path, out_name, frame_start, frame_end, xmin, ymin, xmax, ymax)        
        
if __name__ == "__main__":
    #提前生成文件路径，防止多进程的时候报错文件夹路径不存在
    labelmap, class_whitelist = read_labelmap(open("ava_customdataset_action_list.pbtxt"))
    #图片扩充范围减少一半
    dst_dir_path="./result_video_v2"
    checkdir(dst_dir_path)

    for label_dic in labelmap:
        class_name=label_dic['name']
        dst_class_path = os.path.join(dst_dir_path, class_name)
        checkdir(dst_class_path)

    vid_path1="/home/jovyan/data-vol-1/ava_custom/video_xianchang"
    vid_path2="/home/jovyan/data-vol-1/ava_custom/video_train"
    vid_path3="/home/jovyan/data-vol-1/ava_custom/video_val"
    vid_list1 = GetFileFromThisRootDir(vid_path1, '.mp4')
    vid_list2 = GetFileFromThisRootDir(vid_path2, '.mp4')
    vid_list3 = GetFileFromThisRootDir(vid_path3, '.mp4')
    vid_list=vid_list1+vid_list2+vid_list3
    
    vid_name_dic={}
    for vid_path_name in vid_list:
        vid_name=os.path.basename(vid_path_name)
        name, ext = os.path.splitext(vid_name)
        vid_name_dic[name]=vid_path_name

    csv_path="/home/jovyan/data-vol-1/action_reg/result_csv_v2/"
    csv_list = GetFileFromThisRootDir(csv_path, '.txt')
    csv_num=0
    mul_thread=True
    for csv_name in csv_list:
        person_id=0
        csv_num+=1
        print("[{}/{}]-{}".format(csv_num,len(csv_list),os.path.basename(csv_name)))
        
        if os.path.basename(csv_name)=="武汉海关天河机场海关入境到达24_1DD170B0_1614582377_2.mp4":
            print("There is a problem in {} for decode video.".format(os.path.basename(csv_name)))
            continue
            
        
        with open(csv_name) as f:
            lines = f.readlines()[1:]
            if mul_thread:
                line_list=[]
                for line in lines:
                    line=[line,person_id]
                    line_list.append(line)
                    person_id+=1

                p = Pool(n_thread)
                from functools import partial

                worker = partial(line_mul,vid_name_dic=vid_name_dic)
                for _ in tqdm(p.imap_unordered(worker, line_list), total=len(line_list)):
                    pass
                # p.map(worker, vid_list)
                p.close()
                p.join()
            else:
                for line in tqdm(lines):
                    line = line.rstrip()
                    items = line.split(',')
                    video_path=vid_name_dic[items[1]]
                    label_name=items[0]

                    class_name=label_name.replace("异常行为=","")
                    dst_class_path = os.path.join(dst_dir_path, class_name)
                    checkdir(dst_class_path)

                    out_name=os.path.join(dst_class_path,f"{items[1]}_{person_id}.mp4")
                    person_id+=1
                    frame_start = int(items[2])
                    frame_end = int(items[3])
                    
                    xmin = int(float(items[4]))
                    ymin = int(float(items[5]))
                    xmax = int(float(items[6]))
                    ymax = int(float(items[7]))

                    vid2shortvid(video_path,out_name,frame_start, frame_end, xmin,ymin,xmax,ymax)







