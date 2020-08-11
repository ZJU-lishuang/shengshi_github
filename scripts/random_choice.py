#在一个文件夹下随机选择文件
import random
import os
import shutil

def random_copyfile(srcPath,dstPath,numfiles):
    name_list=list(os.path.join(srcPath,name) for name in os.listdir(srcPath))
    random_name_list=list(random.sample(name_list,numfiles))
    if not os.path.exists(dstPath):
        os.mkdir(dstPath)
    for oldname in random_name_list:
        shutil.copyfile(oldname,oldname.replace(srcPath, dstPath))

srcPath='/home/lishuang/Disk/nfs/traindataset/double300/double_tx2'         
dstPath = '/home/lishuang/Disk/nfs/traindataset/double300/double_tx2_100'
random_copyfile(srcPath,dstPath,100)

