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
    myfont = font_manager.FontProperties(fname='SimHei.ttf')
    plt.bar(range(len(num_list)), num_list,label="train",color='SkyBlue',align='center')
    for a, b in zip(range(len(num_list)), num_list):
        plt.text(a, b + 0.05, '%.0f' % b, ha='center', va='bottom', fontsize=10)
    plt.xticks(range(len(num_list)),name_list,fontproperties=myfont)
    plt.xlabel('class')
    plt.ylabel('num')
    plt.title('the number of each class')
    plt.savefig("num_class.png", dpi=300)
    plt.legend(prop=myfont)
    plt.show()


def class_and_num(root, json_file_se,class_all_name):
    """
    计算每个类别的目标个数
    """
    print('计算每个目标的个数')
    # names = json_load(class_all_name)
    with open(class_all_name, 'r') as f:
        names = np.array([x for x in f.read().strip().splitlines()], dtype=np.str)
        names=names.tolist()# labels
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
                        default="../sample/yolo",
                        help='root dir')
    opt = parser.parse_args()

    root = opt.root
    json_file_se = "json/*.json"
    num_list = class_and_num(root, json_file_se,os.path.join(root,'classes.names'))

    name_list, count_list = [], []
    for i in num_list:
        name=i.split(":")[0]
        num = int(i.split(":")[-1])
        name_list.append(name)
        count_list.append(num)
    draw_bar(name_list, count_list)


