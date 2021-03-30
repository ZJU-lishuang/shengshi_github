import os
import json
import glob
import shutil
import numpy as np
from tqdm import tqdm
import argparse
import matplotlib.pyplot as plt
from matplotlib import font_manager


def json_load(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
    return data


def json_dump(data, json_out):
    json.dump(data, open(json_out, "w"), indent=2, ensure_ascii=False)


def draw_bar(name_list, num_list):
    # plt.bar(range(len(num_list)), num_list, color='green', tick_label=name_list)
    myfont = font_manager.FontProperties(fname='SimHei.ttf')
    plt.bar(range(len(num_list)), num_list,label="train",color='SkyBlue',align='center')
    for a, b in zip(range(len(num_list)), num_list):
        plt.text(a, b + 0.05, '%.0f' % b, ha='center', va='bottom', fontsize=10)
    plt.xticks(range(len(num_list)),name_list,fontproperties=myfont)
    plt.xlabel('class')
    plt.ylabel('num')
    plt.title('the number of each class')
    plt.savefig("num_class.png", dpi=300)
    plt.show()


def class_and_num(root, txt_file_se,class_all_name):
    """
    计算每个类别的目标个数
    """
    print('计算每个目标的个数')
    # names = json_load(class_all_name)
    with open(class_all_name, 'r') as f:
        names = np.array([x for x in f.read().strip().splitlines()], dtype=np.str)  # labels
    a = np.zeros((len(names)), dtype=np.int)
    
    txt_file_se = os.path.join(root, txt_file_se)
    txt_files = glob.glob(txt_file_se)
    ne=0
    for txt_file in tqdm(txt_files):
        with open(txt_file, 'r') as f:
            l = np.array([x.split() for x in f.read().strip().splitlines()], dtype=np.float32)  # labels
        if len(l):
            assert l.shape[1] == 5, 'labels require 5 columns each'
            assert (l >= 0).all(), 'negative labels'
            assert (l[:, 1:] <= 1).all(), 'non-normalized or out of bounds coordinate labels'
            assert np.unique(l, axis=0).shape[0] == l.shape[0], 'duplicate labels'
        else:
            ne += 1  # label empty
            l = np.zeros((0, 5), dtype=np.float32)
        for single_l in l:
            idx=int(single_l[0])
            a[idx]+=1

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
                        default="../sample/yolo",
                        help='root dir')
    opt = parser.parse_args()

    root = opt.root
    txt_file_se = "labels/*.txt"
    num_list = class_and_num(root, txt_file_se,os.path.join(root,'classes.names'))

    name_list, count_list = [], []
    for i in num_list:
        name=i.split(":")[0]
        num = int(i.split(":")[-1])
        name_list.append(name)
        count_list.append(num)
    draw_bar(name_list, count_list)


