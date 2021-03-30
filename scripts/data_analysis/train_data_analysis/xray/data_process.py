import os
import json
import glob
import shutil
from tqdm import tqdm
import argparse

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def json_load(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
    return data


def json_dump(data, json_out):
    json.dump(data, open(json_out, "w"), indent=2, ensure_ascii=False)


def get_all_class(id_list):
    classes = []
    for task_id in id_list:
        json_file = "%s/instances_default.json" % task_id
        json_file = os.path.join(root, json_file)
        data = json_load(json_file)
        for cate in data['categories']:
            name = cate['name']
            if name not in classes:
                classes.append(name)
    print("X光机的类别数：%s" % len(classes))
    print(classes)
    json_dump(classes, "xray.names")
    return classes


def get_del_class(classes, class_all_names):
    del_class = []
    names = json_load(class_all_names)
    for cls in classes:
        if cls not in names:
            del_class.append(cls)
    print("删除的类别有：")
    print(del_class)
    return del_class


def data_clean(id_list, class_all_names):
    """
    将没有任何标签的图片转移到temp文件夹中，备用。
    将只有无效标签的图片和对应的标签删除。
    """
    print("data clean!!!")
    names = json_load(class_all_names)
    for task_id in tqdm(id_list):
        json_file_se="%s/json/*.json" % task_id
        json_file_se = os.path.join(root, json_file_se)
        json_files = glob.glob(json_file_se)
        for json_file in json_files:
            flag = False
            img_info = json_load(json_file)
            anns = img_info['anns']
            if len(anns) == 0:
                # os.remove(json_file)
                shutil.move(json_file, os.path.join(root,"emptyanns", os.path.basename(json_file)))
                img_path = json_file.replace('.json', '.jpg').replace('json/','imageset/')
                if os.path.exists(img_path):
                    shutil.move(img_path, os.path.join(root,'emptyimg', img_info['img']))
                print("move file:%s" % img_path)
            else:
                for ann in anns:
                    name = ann['name']
                    if name in names:
                        flag = True
                        break

                if flag == False:
                    # os.remove(json_file)
                    shutil.move(json_file, os.path.join(root,"uselessanns", os.path.basename(json_file)))
                    img_path = json_file.replace(".json", ".jpg").replace('json/','imageset/')
                    # os.remove(img_path)
                    if os.path.exists(img_path):
                        shutil.move(img_path, img_path.replace('imageset/', 'uselessimg/'))
                    print("remove file:%s" % img_path)
    print("完成数据清理！！！")


def get_del_img(id_list, del_class):
    """
    获取含有一下标签的图片和标注信息
    ['玻璃乳液瓶组', '金属瓶组', '粉末类', '玻璃瓶组', '塑料化妆品瓶组', '化妆瓶喷剂组', '工具堆', '其他铁制品', '金属化妆品瓶组']
    """
    for task_id in tqdm(id_list):
        json_file_se = "%s/json/*.json" % task_id
        json_file_se = os.path.join(root, json_file_se)
        json_files = glob.glob(json_file_se)
        # task_id = os.path.join(root, task_id)
        for json_file in json_files:
            img_info = json_load(json_file)
            anns = img_info['anns']
            for ann in anns:
                name = ann['name']
                if name in del_class:
                    shutil.move(json_file, os.path.join(root,"testjson", os.path.basename(json_file)))
                    img_path = json_file.replace('.json', '.jpg').replace('json/','imageset/')
                    if os.path.exists(img_path):
                        shutil.move(img_path, os.path.join(root,'testimg', img_info['img']))
                    break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--task_id', type=int,
                        # default=[503,517,525,526,527,528,529,530,531,532,541,543,544,555,556,557,558],
                        default=[8],
                        help='task_id for xray')
    parser.add_argument('--root', type=str,
                        # default="/home/lishuang/Disk/gitlab/traincode/CenterNet2/datasets/xray",
                        default="/home/lishuang/Disk/gitlab/traincode/CenterNet2/datasets/xrayval",
                        help='root dir')
    opt = parser.parse_args()
    root = opt.root
    id_list = opt.task_id

    check_dir(os.path.join(root,'emptyimg'))
    check_dir(os.path.join(root, 'emptyanns'))
    check_dir(os.path.join(root, 'uselessimg'))
    check_dir(os.path.join(root, 'uselessanns'))
    check_dir(os.path.join(root, 'testimg'))
    check_dir(os.path.join(root, 'testjson'))

    # 查看数据库里所有的类别
    classes = get_all_class(id_list)

    # 查看去掉了哪些类别
    del_class = get_del_class(classes, os.path.join(root,'xray_all.names'))

    # 数据清理
    data_clean(id_list, os.path.join(root,'xray_all.names'))

    # 获取含有无效标签的图片，用来做实验, 图片存放在test文件夹中
    get_del_img(id_list, del_class)