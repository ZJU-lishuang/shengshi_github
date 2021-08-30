* 根据人工标注，分离每个人的标注，生成划分视频时所需要的标注

`gen_label_ava.py`

* 根据新生成的文件，将视频划分成一个个短视频

`vid2img_ava.py`

* 将短视频转为图片

`build_rawframes.sh`

* 生成文件列表

`vid2img_kinetics_list.py`

* 使用生成的文件列表生成训练格式的文件列表

`gen_label_kinetics.py`