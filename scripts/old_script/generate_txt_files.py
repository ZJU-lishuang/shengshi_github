import os
import argparse
from multiprocessing import Pool,Process

import json

parser = argparse.ArgumentParser(description="Generating csv file for triplet loss!")
parser.add_argument("-e",'--dataroot',  type=str,
                    help="(REQUIRED) Absolute path to the dataset folder to generate a csv file containing the paths\
                     of the images for triplet loss.",
                    default='/home/lishuang/Disk/shengshi_data/split_folder/keypoint_lishuang/'
                    )
parser.add_argument("-net",'--txt_path', type=str,
                    help="Required absolute path of the txt file to be generated.",
                    default='/home/lishuang/Disk/shengshi_data/split_folder/'
                    )
args = parser.parse_args()
dataroot = args.dataroot
txt_path = args.txt_path

def has_file_allowed_extension(filename, extensions):
    """Checks if a file is an allowed extension.

    Args:
        filename (string): path to a file

    Returns:
        bool: True if the filename ends with a known image extension
    """
    filename_lower = filename.lower()#转换字符串中所有大写字符为小写
    return any(filename_lower.endswith(ext) for ext in extensions)


def subdirs(path):
    """Yield directory names not starting with '.' under given path."""
    for entry in os.scandir(path):
        if not entry.name.startswith('.') and entry.is_dir():
            yield entry.name

#返回类别数和类别对应的索引值
def find_classes(dir):
    #找出所有类别，这块可以自己先找好，保存到txt文件中
    #classes = [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
    classes=[d for d in subdirs(dir) ]
    #给类别排个序
    classes.sort()
    #给每个类别赋一个索引值
    class_to_idx = {classes[i]: i for i in range(len(classes))}
    return classes, class_to_idx

def make_dataset(dir, class_to_idx, extensions):
    images = []
    dir = os.path.expanduser(dir)#把path中包含的"~"和"~user"转换成用户目录

    #遍历获得所有图片
    for target in sorted(os.listdir(dir)):
        d = os.path.join(dir, target)
        if not os.path.isdir(d):
            continue

        for root, _, fnames in sorted(os.walk(d)):#os.walk 的返回值是一个生成器(generator),也就是说我们需要不断的遍历它，来获得所有的内容。
            for fname in sorted(fnames):
                if has_file_allowed_extension(fname, extensions):
                    path = os.path.join(root, fname)
                    item = [path, class_to_idx[target]]
                    images.append(item)

    return images #返回元祖（tuple）结构的list，每个元祖包含信息类似：（“图片绝对路径”，类别索引）

def make_dataset_new(dir, classes,class_to_idx, extensions,startids):
    images = []
    dir = os.path.expanduser(dir)#把path中包含的"~"和"~user"转换成用户目录

    
    for target in classes:
        d = os.path.join(dir, target)
        print(startids,": ", d)
        startids=startids+1
        for root, _, fnames in sorted(os.walk(d)):#os.walk 的返回值是一个生成器(generator),也就是说我们需要不断的遍历它，来获得所有的内容。
            for fname in sorted(fnames):
                if has_file_allowed_extension(fname, extensions):
                    path = os.path.join(root, fname)
                    item = [path, class_to_idx[target]]
                    images.append(item)

    return images #返回元祖（tuple）结构的list，每个元祖包含信息类似：（“图片绝对路径”，类别索引）

def make_dataset_thread(arglist):
    dir, classes,class_to_idx, extensions,start=arglist
    return make_dataset_new(dir, classes,class_to_idx, extensions,start)

def save(filename, docs):
    fh = open(filename, 'w')
    for key, value in docs.items():
        fh.write(key+","+str(value))
        fh.write('\n')
    fh.close()

def save_list(filename, docs):
    fh = open(filename, 'w')
    for doc in docs:
        #fh.write(doc[0]+","+str(doc[1]))
        fh.write(doc[0]+" "+str(doc[1]))
        fh.write('\n')
    fh.close()

def convert_label_json_format(out_dir, docs):
    json_name='labels.json'
    ann_dict = {}
    images = []
    annotations = []
    img_id = 0
    ann_id = 0
    cat_id = 1
    category_dict = {}
    for doc in docs:
        image = {}
        image['id'] = img_id
        img_id += 1

        image['width'] = 128
        image['height'] = 128
        filepath=doc[0]
        image['file_name'] =filepath
        images.append(image)


        ann = {}
        ann['id'] = ann_id
        ann_id += 1
        ann['image_id'] = image['id']
        if str(doc[1]) not in category_dict:
                category_dict[str(doc[1])] = cat_id
                cat_id += 1
        ann['category_id'] = category_dict[str(doc[1])]
        ann['bbox']=[0,0,10,10]
        annotations.append(ann)
    ann_dict['images'] = images
    
    categories = [{"id": category_dict[name], "name": name} for name in category_dict]
    categories[0]['supercategory']='face'
    ann_dict['categories'] = categories
    ann_dict['annotations'] = annotations
    print("Num categories: %s" % len(categories))
    print("Num images: %s" % len(images))
    print("Num annotations: %s" % len(annotations))
    jsFile = os.path.join(out_dir, json_name)
    with open(jsFile, 'w') as outfile:
        outfile.write(json.dumps(ann_dict, sort_keys=True))      

def generate_txt_file(dataroot=None, txt_path=None):
    extensions = ['.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif']
    classes, class_to_idx = find_classes(dataroot)
    
    num_process=4
    avg = int(len(classes)/num_process)
    late = len(classes)%num_process
    p = Pool(num_process)
    res_l = []
    for i in range(num_process):
        start = i*avg
        if i == num_process- 1:
            end = (i+1)*avg + late
        else:
            end = (i+1)*avg
        file_list_now = classes[start:end]
        arglist=[dataroot,file_list_now,class_to_idx, extensions,start]
        result=p.apply_async(make_dataset_thread, args=(arglist,))
        res_l.append(result)
    p.close()
    p.join()

    samples=[]
    for res in res_l:  
        samples.extend(res.get())
        #print(res.get().shape)

    #samples = make_dataset(dataroot, class_to_idx, extensions)
    #samples = make_dataset_new(dataroot, classes,class_to_idx, extensions)

    #arglist=[dataroot, classes,class_to_idx, extensions]
    #samples=make_dataset_thread(arglist)


    # classes_txt = os.path.join(txt_path, "classes.txt")
    class_to_idx_txt = os.path.join(txt_path, "class_to_idx.txt")
    samples_txt = os.path.join(txt_path, "samples.txt")

    # save(classes_txt, classes)
    save(class_to_idx_txt, class_to_idx)

    save_list(samples_txt, samples)

    convert_label_json_format(txt_path,samples)


if __name__ == '__main__':
    generate_txt_file(dataroot=dataroot, txt_path=txt_path)