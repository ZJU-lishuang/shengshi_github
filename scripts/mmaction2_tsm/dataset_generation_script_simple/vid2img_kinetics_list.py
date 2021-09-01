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

def class_process(dir_path, dst_dir_path, class_name):
    print('*' * 20, class_name, '*'*20)
    class_path = os.path.join(dir_path, class_name)
    if not os.path.isdir(class_path):
        print('*** is not a dir {}'.format(class_path))
        return

#     dst_class_path = os.path.join(dst_dir_path, class_name)
#     if not os.path.exists(dst_class_path):
#         os.mkdir(dst_class_path)

    vid_list = os.listdir(class_path)
    vid_list.sort()

    file_data = ""
    file_data += "label,filename\n"
    for vid_name in vid_list:
        file_data += class_name+','+os.path.splitext(vid_name)[0]+'\n'
    with open('{}/{}.csv'.format(dst_dir_path,class_name), 'w') as f:
        f.write(file_data)


    print('\n')


if __name__ == "__main__":
    dir_path = sys.argv[1]
    dst_dir_path = sys.argv[2]
    
    if not os.path.exists(dst_dir_path):
        os.mkdir(dst_dir_path)

    class_list = os.listdir(dir_path)
    class_list.sort()
    for class_name in class_list:
        class_process(dir_path, dst_dir_path, class_name)

#     class_name = 'test'
#     class_process(dir_path, dst_dir_path, class_name)
