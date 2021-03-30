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
    plt.savefig("num_class.png", dpi=300)
    plt.show()


def class_and_num(root, json_file_se,class_all_name):
    """
    计算每个类别的目标个数
    """
    print('计算每个目标的个数')
    names = json_load(class_all_name)
    a = np.zeros((len(names)), dtype=np.int)
    
    json_file_se = os.path.join(root, json_file_se)
    json_files = glob.glob(json_file_se)
    for json_file in json_files:
        img_info = json_load(json_file)
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
    parser.add_argument('--root', type=str,
                        default="/home/lishuang/Disk/shengshi_github/scripts/data_analysis/sample/yolo",
                        help='root dir')
    opt = parser.parse_args()

    root = opt.root
    json_file_se = "json/*.json"
    num_list = class_and_num(root, json_file_se,os.path.join(root,'xray_all.names'))

    name_list, count_list = [], []
    for i in num_list:
        num = int(i.split(":")[-1])
        name_list.append(1)
        count_list.append(num)
    draw_bar(name_list, count_list)


