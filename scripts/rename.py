#coding:utf-8

import shutil
import os
 
new_dir='/home/lishuang/Disk/github/AlphaPose-pytorch/train_sppe/data/coco/images/'
ann_dir='/home/lishuang/Disk/shengshi_data/datasets/coco/val2014'
i=0
for root, _, files in os.walk(ann_dir):
    for filename in files:
        if filename.endswith('.jpg'):
            imagename=filename.replace('COCO_val2014_','')
            newdir=os.path.join(new_dir,imagename)
            #print(newdir)
            if i%100==0:
                 print("Processed %d images" % (i))
            shutil.copyfile(os.path.join(root,filename),newdir)
            i=i+1
            #os.rename(root+filename,newdir)

