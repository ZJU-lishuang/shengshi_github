import xml.etree.ElementTree as ET
import pickle
import os
from os import listdir, getcwd
from os.path import join
from PIL import Image



path='.'#the path of xml

def xml_cut(documentname,image_w_batch,image_h_batch,pading=0.0):
    #in_file = open('%s/Annotations/%s.xml'%(path,documentname))
    #img = Image.open('%s/JPEGImages/%s.jpg'%(path,documentname))
    img = Image.open('%s.jpg'%(documentname))
    in_file = open('%s.xml'%(documentname))
    tree=ET.parse(in_file)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)
    in_file.close()
    wstart=[]
    wend=[]
    hstart=[]
    hend=[]
    #image_w_batch>=1,image_h_batch>=1
    wstep=w/image_w_batch
    hstep=h/image_h_batch
    for i in range(image_w_batch):
        ws=wstep*i-wstep*pading
        we=wstep*(i+1)+wstep*pading
        if ws<0 or we>w:
            ws=max(wstep*i-wstep*pading*2,0)
            we=min(wstep*(i+1)+wstep*pading*2,w)
        wstart.append(int(ws))
        wend.append(int(we))
        #wstart.append(int(w/image_w_batch*(i)))
        #wend.append(int(w/image_w_batch*(i+1)))
    for i in range(image_h_batch):
        hs=hstep*i-hstep*pading
        he=hstep*(i+1)+hstep*pading
        if hs<0 or he>h:
            hs=max(hstep*i-hstep*pading*2,0)
            he=min(hstep*(i+1)+hstep*pading*2,h)
        hstart.append(int(hs))
        hend.append(int(he))
        #hstart.append(int(h/image_h_batch*(i)))
        #hend.append(int(h/image_h_batch*(i+1)))
   
    for j in range(image_h_batch):
        for i in range(image_w_batch):
            in_file = open('%s.xml'%(documentname))
            tree=ET.parse(in_file)
            root = tree.getroot()
            size = root.find('size')
            #截取图片坐标wend，wstart，hend，hstart
            cropped = img.crop((wstart[i], hstart[j], wend[i], hend[j]))
            size.find('width').text=str(wend[i]-wstart[i])
            size.find('height').text=str(hend[j]-hstart[j])
            for obj in root.findall('object'):
                cls = obj.find('name').text

                xmlbox = obj.find('bndbox')
                xmin=xmlbox.find('xmin').text
                xmax=xmlbox.find('xmax').text
                ymin=xmlbox.find('ymin').text
                ymax=xmlbox.find('ymax').text

                xmin = max(int(xmin), wstart[i])
                xmax = min(int(xmax), wend[i])
                ymin = max(int(ymin), hstart[j])
                ymax = min(int(ymax), hend[j])
                # 两矩形无相交区域的情况
                if xmin>=xmax or ymin>=ymax:
                    root.remove(obj)
                # 两矩形有相交区域的情况
                else:
                    xmlbox.find('xmin').text = str(int(xmin) - wstart[i]+1)
                    xmlbox.find('xmax').text = str(int(xmax) - wstart[i]-1)
                    xmlbox.find('ymin').text = str(int(ymin) - hstart[j]+1)
                    xmlbox.find('ymax').text = str(int(ymax) - hstart[j]-1)

            if root.find('object')== None:
                continue
            #tree.write('%s/Annotations/%s_%d.xml'%(path,documentname,i))
            #cropped.save('%s/JPEGImages/%s_%d.jpg'%(path,documentname,i))
            tree.write('%s_%d.xml'%(documentname,i+j*image_w_batch))
            cropped.save('%s_%d.jpg'%(documentname,i+j*image_w_batch))


documentname='2018_0423_bileiqi_89'
xml_cut(documentname,2,2,0.05)