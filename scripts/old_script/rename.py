#coding:utf-8

import shutil
import os

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

image_dir= '/home/lishuang/Disk/shengshi_data/xilixiang/xingli-20210112/imageset'
new_dir='/home/lishuang/Disk/shengshi_data/xilixiang/xingli-20210112/JPEGImages'
check_dir(new_dir)
i=0
for root, _, files in os.walk(image_dir):
    for filename in files:
        if filename.endswith('.jpg'):
            # imagename=f"kunming20201102_{i}.jpg"
            imagename=filename.replace("-nfs-行李转盘提箱抓拍-天河-威海机场-行李箱检测-行李箱-","")
            newdir=os.path.join(new_dir,imagename)
            #print(newdir)
            if i%100==0:
                 print("Processed %d images" % (i))
            shutil.copyfile(os.path.join(root,filename),newdir)
            i=i+1
            #os.rename(root+filename,newdir)




