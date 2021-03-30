import os
import json
import glob
import shutil
import numpy as np
from tqdm import tqdm
import argparse
import matplotlib.pyplot as plt


def json_load(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
    return data


def json_dump(data, json_out):
    json.dump(data, open(json_out, "w"), indent=2, ensure_ascii=False)


def draw_bar(name_list, num_list):
    plt.bar(range(len(num_list)), num_list, color='green', tick_label=name_list)
    plt.xlabel('class')
    plt.ylabel('num')
    plt.title('the number of each class')
    plt.savefig("num_class9999.png", dpi=300)
    plt.show()


def class_and_num(id_list, class_all_name):
    """
    计算每个类别的目标个数
    """
    print('计算每个目标的个数')
    names = json_load(class_all_name)
    a = np.zeros((len(names)), dtype=np.int)
    for task_id in tqdm(id_list):
        json_file_se = "%s/json/*.json" % task_id
        json_file_se = os.path.join(root, json_file_se)
        json_files = glob.glob(json_file_se)
        for json_file in tqdm(json_files):
            img_info = json_load(json_file)
            if task_id == 9999:
                name=img_info['name']
                if name in names:
                    idx = names.index(name)
                    a[idx] += 1
                continue
            for ann in img_info['anns']:
                name = ann['name']
                if name in names:
                    idx = names.index(name)
                    a[idx] += 1

    num_list = []
    for name, num in zip(names, a.tolist()):
        num_list.append("%s:%s" % (name, num))
    num_list.sort(key=lambda x:int(x.split(":")[-1]), reverse=True)
    for i in num_list:
        print(i)
    return num_list



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--task_id', type=int,
                        default=[503,517,525,526,527,528,529,530,531,532,541,543,544,555,556,557,558],
                        help='task_id for xray')
    parser.add_argument('--root', type=str,
                        default="/home/lishuang/Disk/gitlab/traincode/CenterNet2/datasets/xray",
                        help='root dir')
    opt = parser.parse_args()

    id_list = opt.task_id
    root = opt.root
    id_list.append(9999)
    num_list = class_and_num(id_list, os.path.join(root,'xray_all.names'))

    name_list, count_list = [], []
    for i in num_list:
        num = int(i.split(":")[-1])
        # 由于后期进行了人造数据，所有的类别不少于300个物体
        #if num < 300:
        #    num = 300
        name_list.append(1)
        count_list.append(num)
    draw_bar(name_list, count_list)


