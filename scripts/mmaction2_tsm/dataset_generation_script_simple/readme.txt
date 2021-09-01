解码异常视频
武汉海关天河机场海关入境到达24_1DD170B0_1614582377_2.mp4

gen_label_ava_simple.py用根据标注文件生成对应的短视频跟踪所需要的文件

##step
#gen short video
python vid2img_ava_simple.py
python vid2img_ava_problemvideo.py

#video2img
python build_rawframes.py result_video_v1/ result_rawframes_v1/ --task rgb --level 2 --ext mp4 --use-opencv
python build_rawframes.py result_video_v2/ result_rawframes_v2/ --task rgb --level 2 --ext mp4 --use-opencv --num-worker 48
python build_rawframes.py result_video_v2_clean/ result_rawframes_v2_clean/ --task rgb --level 2 --ext mp4 --use-opencv --num-worker 48

#gen list for class
python vid2img_kinetics_list.py result_video_v1/ result_video_v1_txt/
python vid2img_kinetics_list.py result_video_v2/ result_video_v2_txt/
python vid2img_kinetics_list.py result_video_v2_clean/ result_video_v2_clean_txt/

#gen train val list  暂时需要修改文件里面参数
python gen_label_kinetics.py