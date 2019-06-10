
from pycocotools.coco import COCO
import numpy as np
import skimage.io as io
import matplotlib.pyplot as plt
import pylab
pylab.rcParams['figure.figsize'] = (8.0, 10.0)


dataDir='..'
dataType='trainval2014'
annFile = '{}/annotations/person_keypoints_{}.json'.format(dataDir,dataType)
coco_kps=COCO(annFile)
catIds = coco_kps.getCatIds(catNms=['person']);
imgIds = coco_kps.getImgIds(catIds=catIds );

for i in range(len(imgIds)):
    if i%1000==0:
        print('i=',i)
    img = coco_kps.loadImgs(imgIds[i])[0]
    I = io.imread('%s/images/%s/%s'%(dataDir,dataType,img['file_name']))
    height = I.shape[0] 
    width = I.shape[1] 
    plt.imshow(I); plt.axis('off')
    fig = plt.gcf() 
    fig.set_size_inches(width/100.0, height/100.0) 
    plt.gca().xaxis.set_major_locator(plt.NullLocator()) 
    plt.gca().yaxis.set_major_locator(plt.NullLocator()) 
    plt.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0) 
    plt.margins(0,0)
    plt.savefig("/home/lishuang/Disk/github/CenterNet-master/data/coco/trainkeybefore/%s"%(img['file_name']),dpi=100)
    ax = plt.gca()
    annIds = coco_kps.getAnnIds(imgIds=img['id'], catIds=catIds, iscrowd=None)
    anns = coco_kps.loadAnns(annIds)
    coco_kps.showAnns(anns)
    fig = plt.gcf() 
    fig.set_size_inches(width/50.0, height/50.0) 
    #plt.gca().xaxis.set_major_locator(plt.NullLocator()) 
    #plt.gca().yaxis.set_major_locator(plt.NullLocator()) 
    #plt.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0) 
    #plt.margins(0,0)
    plt.savefig("/home/lishuang/Disk/github/CenterNet-master/data/coco/trainkey/%s"%(img['file_name']), dpi=100)
    plt.close('all') 