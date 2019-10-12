import os
import xml.etree.ElementTree as ET

def search(path,filename):
    path_file=[]
    for root,dirs,files in os.walk(path):
        if filename in dirs or filename in files:
            root=str(root)
            re_path=os.path.join(root,filename)
            path_file.append(re_path)
    
    return path_file


def Merge_xmls(xml_fs,out_xml):

    if len(xml_fs)==1:
        tree = ET.parse(xml_fs[0])
        tree.write(out_xml)
    else:
        merged_objs=[]
        for xml_f in xml_fs[1:]:
            tree = ET.parse(xml_f)
            root = tree.getroot()

            objs=root.findall('object')
            merged_objs.extend(objs)

        tree = ET.parse(xml_fs[0])
        root = tree.getroot()
        for obj in merged_objs:
            root.append(obj)

        tree.write(out_xml)


def convert_img(image_dir,xml_dir,out_dir):
    ends_in='.jpg'
    imagesnum=0
    annotations=0
    for root, _, files in os.walk(image_dir):
        for filename in files:
            if filename.endswith(ends_in):
                re=search(xml_dir,filename[:-(len(ends_in))] + '.xml')
                if len(re) > 0:
                    Merge_xmls(re,os.path.join(out_dir,filename[:-(len(ends_in))] + '.xml'))
                else:
                    print('{} dont have a xml file'.format(os.path.join(root,filename)))

                imagesnum=imagesnum+1
                annotations=annotations+len(re)
                if imagesnum % 50 == 0:
                    print("Processed %s images, %s annotations" % (imagesnum, annotations))


def get_list(list_dir):
    xml_list=[]
    xml_num=0
    ends_in='.xml'
    list_file = open('%s/xmllist.txt'%(list_dir), 'w')
    for root, _, files in os.walk(list_dir):
        if root.split('/')[-1] == 'JPEGImages':
            for filename in files:
                if filename.endswith(ends_in):
                    xml_name=[os.path.join(root,filename)]
                    xml_list.extend(xml_name)    
                    xml_num=xml_num+1
                    list_file.write('%s\n'%(os.path.join(root,filename)))
                    if xml_num % 50 == 0:
                        print("Processed %s xml" % (xml_num))
    list_file.close()             
    return xml_list
                    
def convert_list(xml_head_dir,xml_dir):
    imagesnum=0
    annotations=0
    for xml_id in xml_head_dir:
        filepath, xmlfilename = os.path.split(xml_id)
        xml_id_old=os.path.join(filepath,xmlfilename)
        xml_id=os.path.join(filepath,'g'+xmlfilename)
        #re=search(xml_dir,xmlfilename)
        #原始的xml
        re=[(xml_id.replace('JPEGImages/','Annotations/')).replace('/TK1/head_pre/','/TX2/Jpg/Train_data/')]  #search slow  #origin xml path
        
        if not os.path.exists(re[0]):
            print('No such file:{}'.format(re[0]))
            imagesnum=imagesnum+1
            annotations=annotations+len(re)
            continue

        if len(re) == 1:
            re.extend([xml_id_old])
            #待生成的xml
            xmlfile=(xml_id.replace('JPEGImages/','Annotations/')).replace('head_pre/','head_pre_xml/')
            #待生成的xml的文件夹
            xmlfilepath=(filepath.replace('JPEGImages','')).replace('head_pre/','head_pre_xml/')
            if not os.path.exists(xmlfilepath):
                os.mkdir(xmlfilepath)


            xmlpath=(filepath.replace('JPEGImages','Annotations')).replace('head_pre/','head_pre_xml/')
            if not os.path.exists(xmlpath):
                os.mkdir(xmlpath)
            
            Merge_xmls(re,xmlfile)
        else:
            print('{} dont have the correct number of xml file'.format(str(xml_id)))
        
        imagesnum=imagesnum+1
        annotations=annotations+len(re)
        if imagesnum % 50 == 0:
            print("Processed %s images, %s annotations" % (imagesnum, annotations))

    
if __name__ == '__main__':       
    image_dir='/home/lishuang/Disk/pytorch/test/img'
    xml_dir='/home/lishuang/Disk/pytorch/test/xml'
    out_dir='/home/lishuang/Disk/pytorch/test/out'
    
    
    xml_head_dir='/home/lishuang/Disk/nfs/TK1/head_pre/guangzhou_T2_1007_1009_2_16'
    xml_origin_dir='/home/lishuang/Disk/nfs/Datasets/TX2/Train_data'

    #xml_list=get_list(xml_head_dir)   #xmllist.txt

    xml_list=open('/home/lishuang/Disk/nfs/TK1/head_pre/xmllist1.txt').read().strip().split()
    convert_list(xml_list,xml_origin_dir)
    xml_list=open('/home/lishuang/Disk/nfs/TK1/head_pre/xmllist2.txt').read().strip().split()
    convert_list(xml_list,xml_origin_dir)
    xml_list=open('/home/lishuang/Disk/nfs/TK1/head_pre/xmllist3.txt').read().strip().split()
    convert_list(xml_list,xml_origin_dir)
    xml_list=open('/home/lishuang/Disk/nfs/TK1/head_pre/xmllist4.txt').read().strip().split()
    convert_list(xml_list,xml_origin_dir)
    #convert_img(image_dir,xml_dir,out_dir)


