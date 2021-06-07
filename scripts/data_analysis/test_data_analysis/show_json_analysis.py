from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import copy
import torch
import numpy as np
import os
from multiprocessing import Pool
import cv2
from PIL import Image, ImageDraw, ImageFont

def box_iou(box1, box2):
    # https://github.com/pytorch/vision/blob/master/torchvision/ops/boxes.py
    """
    Return intersection-over-union (Jaccard index) of boxes.
    Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
    Arguments:
        box1 (Tensor[N, 4])
        box2 (Tensor[M, 4])
    Returns:
        iou (Tensor[N, M]): the NxM matrix containing the pairwise
            IoU values for every element in boxes1 and boxes2
    """

    def box_area(box):
        # box = 4xn
        return (box[2] - box[0]) * (box[3] - box[1])

    area1 = box_area(box1.T)
    area2 = box_area(box2.T)

    # inter(N,M) = (rb(N,M,2) - lt(N,M,2)).clamp(0).prod(2)
    inter = (torch.min(box1[:, None, 2:], box2[:, 2:]) - torch.max(box1[:, None, :2], box2[:, :2])).clamp(0).prod(2)
    return inter / (area1[:, None] + area2 - inter)  # iou = inter / (area1 + area2 - inter)

def filter_anns(img_anns,catId,scorethr=0.05):
    select_anns=[]
    if len(img_anns) > 0 and 'score' in img_anns[0]:
        scores=[]
        for img_ann in img_anns:
            if img_ann['category_id'] == catId and img_ann['score'] > scorethr:
                x1, y1, w, h = img_ann['bbox']
                x2 = x1 + w
                y2 = y1 + h
                select_anns.append([x1, y1, x2, y2])
                scores.append(img_ann['score'])
        inds = np.argsort([-d for d in scores], kind='mergesort')
        select_anns = [select_anns[i] for i in inds]
    else:
        for img_ann in img_anns:
            if img_ann['category_id'] == catId:
                x1, y1, w, h = img_ann['bbox']
                x2 = x1 + w
                y2 = y1 + h
                select_anns.append([x1, y1, x2, y2])
    return select_anns

def analyze_single_image_plus(img_path,img_save_path,catId,gt_img_anns,dt_img_anns,scorethr=0.05,iouthr=0.5):
    select_dt_anns=filter_anns(dt_img_anns,catId,scorethr)
    select_gt_anns = filter_anns(gt_img_anns,catId)
    iouThrs = [iouthr]
    T = len(iouThrs)
    D = len(select_dt_anns)
    G = len(select_gt_anns)
    gtm = torch.zeros((T, G))
    dtm = torch.zeros((T, D))
    tps = torch.zeros((T, 1))
    fps = torch.zeros((T, 1))
    fns = torch.zeros((T, 1))
    if len(select_dt_anns) > 0 and len(select_gt_anns) > 0:
        ious = box_iou(torch.Tensor(select_dt_anns), torch.Tensor(select_gt_anns))
        for tind, iouThr in enumerate(iouThrs):
            for dt_index in range(len(select_dt_anns)):
                iouThrtmp = min([iouThr, 1 - 1e-10])
                macthed = -1
                for gt_index in range(len(select_gt_anns)):
                    # iou=ious[dt_index,gt_index]
                    if gtm[tind, gt_index] > 0:
                        continue
                    if ious[dt_index, gt_index] < iouThrtmp:
                        continue
                    iouThrtmp = ious[dt_index, gt_index]
                    macthed = gt_index
                if macthed == -1:
                    continue
                dtm[tind, dt_index] = macthed + 1
                gtm[tind, macthed] = dt_index + 1
            tps[tind] = torch.sum(dtm[tind] > 0, axis=0)
            fps[tind] = torch.sum(dtm[tind] < 1, axis=0)
            fns[tind] = torch.sum(gtm[tind] < 1, axis=0)
    elif len(select_dt_anns) == 0 and len(select_gt_anns) > 0:
        # 漏检
        for tind, iouThr in enumerate(iouThrs):
            fns[tind] = len(select_gt_anns)
    elif len(select_dt_anns) > 0 and len(select_gt_anns) == 0:
        # 误检
        for tind, iouThr in enumerate(iouThrs):
            fps[tind] = len(select_dt_anns)
    else:
        assert len(select_dt_anns) == 0 and len(select_gt_anns) == 0

    if fps[0].item() > 0 or fns[0].item() > 0:
        img=cv2.imread(img_path)
        img_name=os.path.basename(img_path)
        color = [0,0,255] #red
        tl = round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
        fp_flag=False
        for tind, dtmflags in enumerate(dtm):
            for dt_index,dtmflag in enumerate(dtmflags):
                # 误检
                if dtmflag <1:
                    fp_flag=True
                    x,y,x2,y2=select_dt_anns[dt_index]
                    c1, c2 = (int(x), int(y)), (int(x2), int(y2))
                    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
                    str=u"误检"
                    # tf = max(tl - 1, 1)  # font thickness
                    # t_size = cv2.getTextSize(str, 0, fontScale=tl / 3, thickness=tf)[0]
                    # c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                    # cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
                    # cv2.putText(img, "false positive", (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255],
                    #             thickness=tf, lineType=cv2.LINE_AA)

                    ## Use simsum.ttc to write Chinese.
                    b, g, r, a = 255, 255, 255,0
                    fontpath = "./SimHei.ttf"
                    font = ImageFont.truetype(fontpath, 40)
                    img_pil = Image.fromarray(img)
                    draw = ImageDraw.Draw(img_pil)
                    label_size = draw.textsize(str, font)
                    draw.rectangle(
                        [c1[0], c1[1], c1[0] + label_size[0], c1[1] - label_size[1]],
                        outline=tuple(color),
                        width=1,
                        fill=tuple(color)  # 用于填充
                    )
                    draw.text((c1[0], c1[1] - 40), str, font=font, fill=(b, g, r))
                    img = np.array(img_pil)

        fn_flag = False
        for tind, gtmflags in enumerate(gtm):
            for gt_index,gtmflag in enumerate(gtmflags):
                # 漏检
                if gtmflag <1:
                    fn_flag = True
                    x, y, x2, y2 = select_gt_anns[gt_index]
                    c1, c2 = (int(x), int(y)), (int(x2), int(y2))
                    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
                    str = u"漏检"
                    # tf = max(tl - 1, 1)  # font thickness
                    # t_size = cv2.getTextSize(str, 0, fontScale=tl / 3, thickness=tf)[0]
                    # c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                    # cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
                    # cv2.putText(img, "false negative", (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255],
                    #             thickness=tf, lineType=cv2.LINE_AA)

                    ## Use simsum.ttc to write Chinese.
                    b, g, r, a = 255, 255, 255,0
                    fontpath = "./SimHei.ttf"
                    font = ImageFont.truetype(fontpath, 40)
                    img_pil = Image.fromarray(img)
                    draw = ImageDraw.Draw(img_pil)
                    label_size = draw.textsize(str, font)
                    draw.rectangle(
                        [c1[0], c1[1], c1[0] + label_size[0], c1[1] - label_size[1]],
                        outline=tuple(color),
                        width=1,
                        fill=tuple(color) # 用于填充
                    )
                    draw.text((c1[0], c1[1] - 40), str, font=font, fill=(b, g, r))
                    img = np.array(img_pil)
        if fp_flag:
            img_fp_save_path = os.path.join(img_save_path, "误检")
            if not os.path.exists(img_fp_save_path):
                os.makedirs(img_fp_save_path)
            img_fp_save_img = os.path.join(img_fp_save_path, img_name)
            cv2.imwrite(img_fp_save_img, img)
        if fn_flag:
            img_fn_save_path = os.path.join(img_save_path, "漏检")
            if not os.path.exists(img_fn_save_path):
                os.makedirs(img_fn_save_path)
            img_fn_save_img = os.path.join(img_fn_save_path, img_name)
            cv2.imwrite(img_fn_save_img, img)

    return tps,fps,fns


def analyze_individual_category(img_root,save_root,k,catId,cocoGt,cocoDt,scorethr=0.05,ovthresh=0.5):
    nm = cocoGt.loadCats(catId)[0]
    print(f'--------------analyzing {k + 1}-{nm["name"]}---------------')
    single_class_outputs = {}
    imgIds = cocoGt.getImgIds()
    # dt = copy.deepcopy(cocoDt)
    # gt = copy.deepcopy(cocoGt)
    dt=cocoDt
    gt=cocoGt
    cocoGt.loadImgs()
    #coco map caculate slow
    # dt_anns = dt.dataset['annotations']
    # select_dt_anns = []
    # for ann in dt_anns:
    #     if ann['category_id'] == catId:
    #         select_dt_anns.append(ann)
    # dt.dataset['annotations'] = select_dt_anns
    # dt.createIndex()
    # gt_anns = gt.dataset['annotations']
    # select_gt_anns = []
    # for ann in gt_anns:
    #     if ann['category_id'] == catId:
    #         select_gt_anns.append(ann)
    # gt.dataset['annotations'] = select_gt_anns
    # gt.createIndex()
    # cocoEval = COCOeval(gt, dt, 'bbox')
    # cocoEval.params.useCats = 1
    # cocoEval.evaluate()
    # cocoEval.accumulate()
    # cocoEval.summarize()

    #single image
    total_tps=0
    total_fps=0
    total_fns=0
    total_gt=len(gt.catToImgs[catId])
    for j,imgid in enumerate(imgIds):
        dt_img_anns = dt.imgToAnns[j]
        gt_img_anns = gt.imgToAnns[j]
        img_name=dt.loadImgs(imgid)[0]["file_name"]
        img_path=os.path.join(img_root,img_name)
        img_class_save_dir=os.path.join(save_root, nm["name"])
        if not os.path.exists(img_class_save_dir):
            os.makedirs(img_class_save_dir)
        # tps,fps,fns=analyze_single_image_plus(img_path,img_class_save_dir,catId, gt_img_anns, dt_img_anns, scorethr,ovthresh)
        #new iou for detect result
        select_dt_anns=[]
        if len(dt_img_anns) > 0 :
            for img_ann in dt_img_anns:
                x1, y1, w, h = img_ann['bbox']
                x2 = x1 + w
                y2 = y1 + h
                select_dt_anns.append([x1, y1, x2, y2])
            ious = box_iou(torch.Tensor(select_dt_anns), torch.Tensor(select_dt_anns))  > ovthresh
            delid=[]
            for dt_index in range(len(select_dt_anns)):
                for gt_index in range(len(select_dt_anns)):
                    if gt_index <= dt_index:
                        continue
                    if gt_index in delid:
                        continue
                    if dt_img_anns[dt_index]['category_id']!=dt_img_anns[gt_index]['category_id']:
                        continue
                    if ious[dt_index,gt_index]:
                        delid.append(gt_index)
            dt_img_anns_filter=[dt_img_ann for id,dt_img_ann in enumerate(dt_img_anns) if id not in delid]
        else:
            dt_img_anns_filter=dt_img_anns
        tps,fps,fns=analyze_single_image_plus(img_path,img_class_save_dir,catname,catId, gt_img_anns, dt_img_anns_filter, scorethr,ovthresh)
        total_tps+=tps
        total_fps+=fps
        total_fns+=fns

    single_class_outputs["检出"] = total_tps.item()
    single_class_outputs["误检"] = total_fps.item()
    single_class_outputs["漏检"] = total_fns.item()
    single_class_outputs["总数"] = total_gt
    print(single_class_outputs)
    return single_class_outputs


def main():
    root = "../data/clothing_test"
    img_root="../data/clothing_test/show/images"
    save_root="../data/clothing_test/autolabels/result"
    filehead='exp8'
    result_json=f"result_{filehead}.json"
    gt_json = "clothing_val.json"
    # filehead=os.path.join(root,'autolabels',filehead)
    result_json=os.path.join(root,"autolabels",result_json)
    gt_json=os.path.join(root,gt_json)
    cocoGt = COCO(gt_json)
    cocoDt = cocoGt.loadRes(result_json)

    # scorethrs=[0.3,0.4,0.5,0.6,0.7,0.8]
    # ovthreshs=[0.1,0.3,0.5]
    scorethrs=[0.5]
    ovthreshs=[0.1]

    for scorethr in scorethrs:
        for ovthresh in ovthreshs:

            catIds = cocoGt.getCatIds()
            #single class
            outputs={}
            mAP=[]

            # with Pool(processes=4) as pool:
            #     args = [(k,catId,cocoGt,cocoDt,scorethr,ovthresh)
            #             for k, catId in enumerate(catIds)]
            #     analyze_results = pool.starmap(analyze_individual_category_with_ap, args)

            # for k, catId in enumerate(catIds):
            #     nm = cocoGt.loadCats(catId)[0]
            #     print(f'--------------saving {k + 1}-{nm["name"]}---------------')
            #     analyze_result = analyze_results[k]
            #     outputs[nm["name"]]=analyze_result
            #     if "ap" in outputs[nm["name"]]:
            #         ap=outputs[nm["name"]]["ap"]
            #         mAP.append(ap)
        
            # 单线程
            for k, catId in enumerate(catIds):
                nm = cocoGt.loadCats(catId)[0]

                outputs[nm["name"]] = analyze_individual_category(img_root,save_root,k, catId, cocoGt, cocoDt, scorethr, ovthresh)
                
                if "ap" in outputs[nm["name"]]:
                    ap=outputs[nm["name"]]["ap"]
                    mAP.append(ap)



if __name__ == '__main__':
    main()