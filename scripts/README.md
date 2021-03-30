### coco_keypoint folder
*在coco数据集上，把关键点打印到图片上。参考[cocoapi](https://github.com/cocodataset/cocoapi)的使用。*

### data_analysis folder
*数据分析文件夹，统计各个类别数目，检出，误检，漏检，ap*

### data_convert folder

- **xml2txt.py**

    将xml格式标注转为yolo格式标注，并生成训练文件列表和验证文件列表

- **cvat2txt.py**

    交通项目，将cvat格式数据转为yolo格式

- **xml2json.py**

    将xml格式文件转为json格式文件

- **voc_to_coco_xml.py**

    将voc数据格式转为coco数据格式。

- **voc_to_coco_thread.py**

    将voc数据格式转为coco数据格式。使用多进程提升速度。


### old_script folder
*存放旧的脚本文件,后续使用时再整理出来*



