# Code for "TSM: Temporal Shift Module for Efficient Video Understanding"
# arXiv:1811.08383
# Ji Lin*, Chuang Gan, Song Han
# {jilin, songhan}@mit.edu, ganchuang@csail.mit.edu
# ------------------------------------------------------
# Code adapted from https://github.com/metalbubble/TRN-pytorch/blob/master/process_dataset.py

import os
import random

def checkdir(dirpath):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
# dataset_path = '/home/lishuang/Disk/gitlab/traincode/mmaction2/data/fight-detection/fight-detection-rawframes'
# label_path = '/home/lishuang/Disk/gitlab/traincode/mmaction2/data/fight-detection'
version="2_clean"
dataset_path = f'result_rawframes_v{version}'
label_path = f'result_video_v{version}_txt'
trainval_path= f'result_video_v{version}_trainval'

if __name__ == '__main__':
    with open('violent_label_map.txt') as f:
        categories = f.readlines()
        categories = [c.strip().replace(' ', '_').replace('"', '').replace('(', '').replace(')', '').replace("'", '') for c in categories]
    assert len(set(categories)) == 12
    dict_categories = {}
    for i, category in enumerate(categories):
        dict_categories[category] = i

    print(dict_categories)

    #根据标签得到的文件列表,生成训练列表和验证列表
#     files_input = ['打斗.csv', '发传单.csv', '举标语.csv', '正常.csv']
    files_input = os.listdir(label_path)
    file_val_data = "label,filename\n"
    file_train_data = "label,filename\n"
    file_train_data_tmp=[]
    file_val_data_tmp=[]
    for filename_input in files_input:
        with open(os.path.join(label_path, filename_input)) as f:
            lines = f.readlines()[1:]
        lines_num=len(lines)
        train_num=int(lines_num*0.9)
        file_train_data_tmp.extend(lines[:train_num])
        file_val_data_tmp.extend(lines[train_num:])
        # file_train_data+=''.join(lines[:train_num])
        # file_val_data += ''.join(lines[train_num:])
    checkdir(trainval_path)
    class_name="train"
    random.shuffle(file_train_data_tmp)
    file_train_data += ''.join(file_train_data_tmp)
    with open(os.path.join(trainval_path, '{}.csv'.format(class_name)), 'w') as f:
        f.write(file_train_data)
    class_name = "val"
    random.shuffle(file_val_data_tmp)
    file_val_data += ''.join(file_val_data_tmp)
    with open(os.path.join(trainval_path, '{}.csv'.format(class_name)), 'w') as f:
        f.write(file_val_data)

    files_input = ['val.csv', 'train.csv']
    files_output = ['val_videofolder.txt', 'train_videofolder.txt']
    for (filename_input, filename_output) in zip(files_input, files_output):
        count_cat = {k: 0 for k in dict_categories.keys()}
        with open(os.path.join(trainval_path, filename_input)) as f:
            lines = f.readlines()[1:]
        folders = []
        idx_categories = []
        categories_list = []
        for line in lines:
            line = line.rstrip()
            items = line.split(',')
            # folders.append(items[1] + '_' + items[2])
            folders.append(items[1])
            this_catergory = items[0].replace(' ', '_').replace('"', '').replace('(', '').replace(')', '').replace("'", '')
            categories_list.append(this_catergory)
            idx_categories.append(dict_categories[this_catergory])
            count_cat[this_catergory] += 1
        print(max(count_cat.values()))

        assert len(idx_categories) == len(folders)
        missing_folders = []
        output = []
        for i in range(len(folders)):
            curFolder = folders[i]
            curIDX = idx_categories[i]
            # counting the number of frames in each video folders
            img_dir = os.path.join(dataset_path, categories_list[i], curFolder)
            if not os.path.exists(img_dir):
                missing_folders.append(img_dir)
                # print(missing_folders)
            else:
                dir_files = os.listdir(img_dir)
                output.append('%s %d %d'%(os.path.join(categories_list[i], curFolder), len(dir_files), curIDX))
            print('%d/%d, missing %d'%(i, len(folders), len(missing_folders)))
        with open(os.path.join(trainval_path, filename_output),'w') as f:
            f.write('\n'.join(output))
        with open(os.path.join(trainval_path, 'missing_' + filename_output),'w') as f:
            f.write('\n'.join(missing_folders))
