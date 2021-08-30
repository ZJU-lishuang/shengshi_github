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

def vid2trackvid(frame_list,video_path,box_w,box_h,out_name,position_x_list,position_y_list):
    frame_list = np.array(frame_list)
    frame_start = frame_list.min()
    frame_end = frame_list.max()
    cap = cv2.VideoCapture(video_path)  # 打开视频文件
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # 获得视频文件的帧数
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获得视频文件的帧率
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # 获得视频文件的帧宽
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # 获得视频文件的帧高

    # 创建保存视频文件类对象
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # fourcc = cv2.VideoWriter_fourcc(*'H264')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # update box scale
    cut_width = box_w
    cut_height = box_h
    ratio_big = 0.5
    ratio_small = 0.25
    ratio_ww = 1
    ratio_hh = 1
    if cut_width / width > 0.25:
        ratio_ww = 0.5
    if cut_height / height > 0.25:
        ratio_hh = 0.5
    if cut_width > cut_height:
        ratio_w = ratio_small * ratio_ww
        ratio_h = ratio_big * ratio_hh
    else:
        ratio_w = ratio_big * ratio_ww
        ratio_h = ratio_small * ratio_hh
    new_width = (2 * ratio_w + 1) * cut_width
    if new_width > width - 1:
        new_width = width - 1
    box_w = int(new_width)
    new_height = (2 * ratio_h + 1) * cut_height
    if new_height > height - 1:
        new_height = height - 1
    box_h = int(new_height)
    if box_w % 2 != 0:
        box_w -= 1
    if box_h % 2 != 0:
        box_h -= 1
    cut_width = box_w
    cut_height = box_h
    out = cv2.VideoWriter(out_name, fourcc, fps, (int(cut_width), int(cut_height)))

    # 计算视频长度/s
    video_length = frames / fps
    # print('start and stop must < %.1f' % video_length)  # 提示输入变量的范围
    start = frame_start / fps
    # print("start time/s: {}".format(start))
    frame_end = min(frames - 1, frame_end)
    stop = frame_end / fps
    # print("stop time/s: {}".format(stop))
    # 设置帧读取的开始位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, start * fps)
    pos = cap.get(cv2.CAP_PROP_POS_FRAMES)  # 获得帧位置
    while (pos <= stop * fps):
        ret, frame = cap.read()  # 捕获一帧图像
        centerx = int(position_x_list[int(pos) - frame_start])
        centery = int(position_y_list[int(pos) - frame_start])
        xmin = int(centerx - box_w / 2)
        xmax = int(centerx + box_w / 2)
        ymin = int(centery - box_h / 2)
        ymax = int(centery + box_h / 2)
        if xmin < 0:
            xmin = 0
            xmax = xmin + box_w
        if xmax > width - 1:
            xmax = width - 1
            xmin = xmax - box_w
        if ymin < 0:
            ymin = 0
            ymax = ymin + box_h
        if ymax > height - 1:
            ymax = height - 1
            ymin = ymax - box_h
        assert xmax - xmin == cut_width and ymax - ymin == cut_height
        frame = frame[int(ymin):int(ymax), int(xmin):int(xmax)]
        out.write(frame)  # 保存帧
        pos = cap.get(cv2.CAP_PROP_POS_FRAMES)

    cap.release()
    out.release()

def kalman_position(frame_list,centerx_list,length):
    frame_list = np.array(frame_list)
    frame_start = frame_list.min()
    frame_end = frame_list.max()

    # 以x坐标为例子
    # 初始的预测位置直接用测量值
    predicts_x = [centerx_list[0]]
    position_predict_x = predicts_x[0]

    # 精准估计的方差，初始化为零
    predict_var_x = 0
    # 直接根据速度估计位置时，添加上噪声，作为位置的方差
    odo_std = max(int(length*0.01),1)
    noise_x = np.random.normal(0, odo_std, size=(frame_end - frame_start))
    odo_var_x = odo_std ** 2
    # 目标移动速度的标准差
    v_std_x = max(int(length*0.01),1)

    position_noise_x_list = []
    position_noise_x_list.append(centerx_list[0])
    # 时间间隔1/25秒
    for i in range(1, frame_end - frame_start+1):
        # 使用精确估计值计算速度
        dv_x = 0
        if i - 2 in predicts_x:
            dv_x = predicts_x[i - 1] - predicts_x[i - 2]
        # 当前时刻速度添加噪声模拟真实场景
        dv_x = dv_x + np.random.normal(0, v_std_x)  # 模拟从IMU读取出的速度
        position_predict_x = position_predict_x + dv_x  # 利用上个时刻的位置和速度预测当前位置
        predict_var_x += v_std_x ** 2  # 更新预测数据的方差
        # 下面是Kalman滤波
        cur = i + frame_start
        pre = i - 1 + frame_start
        while (cur not in frame_list):
            cur += 1
        while (pre not in frame_list):
            pre -= 1
        # 使用标注位置估计线性速度来预测位置
        speed_x = (centerx_list[np.where(frame_list==cur)[0].item()] - centerx_list[np.where(frame_list==pre)[0].item()]) / (cur - pre)
        # 直接预测当前位置，两个标注帧之间默认为线性函数估计(本来应该是检测或标注出当前位置作为预测值)
        position_noise_x = centerx_list[np.where(frame_list==pre)[0].item()] + speed_x * (i + frame_start - pre) + noise_x[i-1]
        position_noise_x_list.append(position_noise_x)
        # 集合直接预测和估计位置精准估计的位置
        position_predict_x = position_predict_x * odo_var_x / (predict_var_x + odo_var_x) + \
                             position_noise_x * predict_var_x / (predict_var_x + odo_var_x)
        # 更新精准估计的方差
        predict_var_x = (predict_var_x * odo_var_x) / (predict_var_x + odo_var_x) ** 2
        # 保存精准估计的位置
        predicts_x.append(position_predict_x)

    return predicts_x,position_noise_x_list

    # import matplotlib.pyplot as plt
    # t = np.linspace(0, int(frame_end - frame_start)+1, int(frame_end - frame_start)+1)
    # plt.plot(frame_list - frame_start, centerx_list, label='truth position')
    # plt.plot(t, position_noise_x_list, label='only use measured position')
    # plt.plot(t, predicts_x, label='kalman filtered position')
    #
    # plt.legend()
    # plt.show()

def csv_mul(csv_path,vid_name_dic):
    frame_list = []
    centerx_list = []
    centery_list = []
    box_w = 0
    box_h = 0
    with open(csv_path) as f:
        lines = f.readlines()[1:]
        for line in lines:
            line = line.rstrip()
            items = line.split(',')
            video_path = vid_name_dic[items[1]]
            label_name = items[0]

            class_name=label_name.replace("异常行为=","")
            dst_class_path = os.path.join(dst_dir_path, class_name)
            checkdir(dst_class_path)

            csv_base_name=os.path.splitext(os.path.basename(csv_path))[0]
            out_name = os.path.join(dst_class_path, f"{csv_base_name}.mp4")
            tmp = 0
            while os.path.exists(out_name):
                out_name = os.path.join(dst_class_path, f"{csv_base_name}_re{tmp}.mp4")
                tmp += 1

            frame_id = int(items[3])
            xmin = int(float(items[4]))
            ymin = int(float(items[5]))
            xmax = int(float(items[6]))
            ymax = int(float(items[7]))
            box_w = max(box_w, xmax - xmin)
            box_h = max(box_h, ymax - ymin)
            frame_list.append(frame_id)
            centerx_list.append((xmin + xmax) / 2)
            centery_list.append((ymin + ymax) / 2)

    # if box_w % 2 != 0:
    #     box_w += 1
    # if box_h % 2 != 0:
    #     box_h += 1

    predicts_x, position_noise_x_list = kalman_position(frame_list, centerx_list, box_w)
    predicts_y, position_noise_y_list = kalman_position(frame_list, centery_list, box_h)

    vid2trackvid(frame_list, video_path, box_w, box_h, out_name, predicts_x, predicts_y)

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


if __name__ == "__main__":
    labelmap, class_whitelist = read_labelmap(open("ava_customdataset_action_list.pbtxt"))
    dst_dir_path="./result_video_track_addv1"
    checkdir(dst_dir_path)

    for label_dic in labelmap:
        class_name=label_dic['name']
        dst_class_path = os.path.join(dst_dir_path, class_name)
        checkdir(dst_class_path)

    vid_path="../action_dataset/videos_addv1"
    vid_list = GetFileFromThisRootDir(vid_path, '.mp4')
    
    vid_name_dic={}
    for vid_path_name in vid_list:
        vid_name=os.path.basename(vid_path_name)
        name, ext = os.path.splitext(vid_name)
        vid_name_dic[name]=vid_path_name

    csv_dir_path = "result_csv_track_shortvideo_addv1"
    csv_list = GetFileFromThisRootDir(csv_dir_path, '.txt')
    mul_thread = True
    if mul_thread:
        p = Pool(n_thread)
        from functools import partial

        worker = partial(csv_mul, vid_name_dic=vid_name_dic)
        for _ in tqdm(p.imap_unordered(worker, csv_list), total=len(csv_list)):
            pass
        # p.map(worker, vid_list)
        p.close()
        p.join()
    else:
        csv_num=0
        for csv_path in csv_list:
            csv_num+=1
            print("[{}/{}]-{}".format(csv_num, len(csv_list), os.path.basename(csv_path)))
            csv_mul(csv_path,vid_name_dic)




