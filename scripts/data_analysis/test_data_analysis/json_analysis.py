from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
import copy
import torch
import numpy as np
import os
from multiprocessing import Pool

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

def voc_ap(rec, prec):
    # correct AP calculation
    # first append sentinel values at the end
    mrec = np.concatenate(([0.], rec, [1.]))
    mpre = np.concatenate(([0.], prec, [0.]))

    # compute the precision envelope
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

    # to calculate area under PR curve, look for points
    # where X axis (recall) changes value
    i = np.where(mrec[1:] != mrec[:-1])[0]

    # and sum (\Delta recall) * prec
    ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap

# 主函数，读取预测和真实数据，计算Recall, Precision, AP
def voc_eval(detpath,
             annopath,
             classname,
             scorethr=0.05,
             ovthresh=0.5):
    """rec, prec, ap = voc_eval(detpath,
                                annopath,
                                imagesetfile,
                                classname,
                                [ovthresh],
                                [use_07_metric])

    Top level function that does the PASCAL VOC evaluation.

    detpath: Path to detections
        detpath.format(classname) 需要计算的类别的txt文件路径.
    annopath: Path to annotations
        annopath.format(imagename) label的xml文件所在的路径
    imagesetfile: 测试txt文件，里面是每个测试图片的地址，每行一个地址
    classname: 需要计算的类别
    cachedir: 缓存标注的目录
    [ovthresh]: IOU重叠度 (default = 0.5)
    [use_07_metric]: 是否使用VOC07的11点AP计算(default False)
    """
    # assumes detections are in detpath.format(classname)
    # assumes annotations are in annopath.format(imagename)
    # assumes imagesetfile is a text file with each line an image name
    # cachedir caches the annotations in a pickle file


    # 对每张图片的xml获取函数指定类的bbox等
    class_recs = {}  # 保存的是 Ground Truth的数据
    npos = 0

    imagenames=annopath.imgToAnns
    for imageid in imagenames:
        R=[ann for ann in imagenames[imageid] if ann['category_id']==classname]
        bbox = np.array([x['bbox'] for x in R])
        #  different基本都为0/False.
        difficult = np.array([x['iscrowd'] for x in R]).astype(np.bool)
        det = [False] * len(R)  # list中形参len(R)个False。
        npos = npos + sum(~difficult)  # 自增，~difficult取反,统计样本个数

        # 记录Ground Truth的内容
        class_recs[imageid] = {'bbox': bbox,
                                 'difficult': difficult,
                                 'det': det}

    image_ids=[]
    confidence=[]
    BB=[]
    dt_anns = detpath.dataset['annotations']
    for ann in dt_anns:
        if ann['category_id'] == classname and ann['score'] > scorethr:
            image_ids.append(ann['image_id'])
            confidence.append(ann['score'])
            BB.append(ann['bbox'])

    confidence=np.array(confidence)
    BB = np.array(BB)
    if len(BB) > 0:
        # 对confidence的index根据值大小进行降序排列。
        sorted_ind = np.argsort(-confidence)
        sorted_scores = np.sort(-confidence)
        BB = BB[sorted_ind, :]  # 重排bbox，由大概率到小概率。
        image_ids = [image_ids[x] for x in sorted_ind]  # 图片重排，由大概率到小概率。
    else:
        return npos,0,0,0
    # go down dets and mark TPs and FPs
    nd = len(image_ids)

    tp = np.zeros(nd)
    fp = np.zeros(nd)
    for d in range(nd):
        R = class_recs[image_ids[d]]  # ann

        '''
        1. 如果预测输出的是(x_min, y_min, x_max, y_max)，那么不需要下面的top,left,bottom, right转换
        2. 如果预测输出的是(x_center, y_center, h, w),那么就需要转换

        3. 计算只能使用[left, top, right, bottom],对应lable的[x_min, y_min, x_max, y_max]
        '''
        bb = BB[d, :].astype(float)

        # 转化为(x_min, y_min, x_max, y_max)
        top = int(bb[1])
        left = int(bb[0])
        bottom = int(bb[1] + bb[3])
        right = int(bb[0] + bb[2])
        bb = [left, top, right, bottom]

        ovmax = -np.inf  # 负数最大值
        BBGT = R['bbox'].astype(float)

        if BBGT.size > 0:
            # compute overlaps
            # intersection
            ixmin = np.maximum(BBGT[:, 0], bb[0])
            iymin = np.maximum(BBGT[:, 1], bb[1])
            ixmax = np.minimum(BBGT[:, 0]+BBGT[:, 2], bb[2])
            iymax = np.minimum(BBGT[:, 1]+BBGT[:, 3], bb[3])
            iw = np.maximum(ixmax - ixmin + 1., 0.)
            ih = np.maximum(iymax - iymin + 1., 0.)
            inters = iw * ih

            # union
            uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.)+
                   (BBGT[:, 2] + 1.) *
                   (BBGT[:, 3] + 1.) - inters)

            overlaps = inters / uni
            ovmax = np.max(overlaps)  # 最大重叠
            jmax = np.argmax(overlaps)  # 最大重合率对应的gt
        # 计算tp 和 fp个数
        if ovmax > ovthresh:
            if not R['difficult'][jmax]:
                # 该gt被置为已检测到，下一次若还有另一个检测结果与之重合率满足阈值，则不能认为多检测到一个目标
                if not R['det'][jmax]:
                    tp[d] = 1.
                    R['det'][jmax] = 1  # 标记为已检测
                else:
                    fp[d] = 1.
        else:
            fp[d] = 1.

    recall_num = sum(tp)
    wujian_num = sum(fp)
    # compute precision recall
    fp_ap = np.cumsum(fp)  # np.cumsum() 按位累加
    tp_ap = np.cumsum(tp)
    rec = tp_ap / float(npos)



    # avoid divide by zero in case the first detection matches a difficult
    # ground truth
    # np.finfo(np.float64).eps 为大于0的无穷小
    prec = tp_ap / np.maximum(tp_ap + fp_ap, np.finfo(np.float64).eps)
    ap = voc_ap(rec, prec)
    print("ap=",ap)
    return npos,recall_num,wujian_num, ap

def filter_anns(img_anns,catId,scorethr=0.05):
    select_anns=[]
    if len(img_anns) > 0 and 'score' in img_anns[0]:
        for img_ann in img_anns:
            if img_ann['category_id'] == catId and img_ann['score'] > scorethr:
                x1, y1, w, h = img_ann['bbox']
                x2 = x1 + w
                y2 = y1 + h
                select_anns.append([x1, y1, x2, y2])
    else:
        for img_ann in img_anns:
            if img_ann['category_id'] == catId:
                x1, y1, w, h = img_ann['bbox']
                x2 = x1 + w
                y2 = y1 + h
                select_anns.append([x1, y1, x2, y2])
    return select_anns

def analyze_single_image(catId,gt_img_anns,dt_img_anns,scorethr=0.05,iouthr=0.5):
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
    return tps,fps,fns

def analyze_individual_category_with_ap(k,catId,cocoGt,cocoDt,scorethr=0.05,ovthresh=0.5):
    nm = cocoGt.loadCats(catId)[0]
    print(f'--------------analyzing {k + 1}-{nm["name"]}---------------')
    single_class_outputs={}
    dt = cocoDt
    gt = cocoGt
    # total_gt, total_tps, total_fps, ap = voc_eval(dt, gt, catId, scorethr, ovthresh)
    if len(gt.catToImgs[catId]) >0:
        total_gt, total_tps, total_fps, ap = voc_eval(dt, gt, catId,scorethr,ovthresh)
    else:
        single_class_outputs=analyze_individual_category(k,catId,cocoGt,cocoDt,scorethr,ovthresh)
        print(single_class_outputs)
        return single_class_outputs

    assert total_gt==len(gt.catToImgs[catId])
    total_fns=total_gt-total_tps
    single_class_outputs["检出"] = total_tps
    single_class_outputs["误检"] = total_fps
    single_class_outputs["漏检"] = total_fns
    single_class_outputs["总数"] = total_gt
    single_class_outputs["ap"] = ap
    print(single_class_outputs)
    return single_class_outputs

def analyze_individual_category(k,catId,cocoGt,cocoDt,scorethr=0.05,ovthresh=0.5):
    nm = cocoGt.loadCats(catId)[0]
    print(f'--------------analyzing {k + 1}-{nm["name"]}---------------')
    single_class_outputs = {}
    imgIds = cocoGt.getImgIds()
    # dt = copy.deepcopy(cocoDt)
    # gt = copy.deepcopy(cocoGt)
    dt=cocoDt
    gt=cocoGt

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
        tps,fps,fns=analyze_single_image(catId, gt_img_anns, dt_img_anns, scorethr,ovthresh)
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
    root = "../sample/yolo"
    filehead="newcar"
    result_json="result.json"
    gt_json = "newcar_val.json"
    filehead=os.path.join(root,filehead)
    result_json=os.path.join(root,result_json)
    gt_json=os.path.join(root,gt_json)
    cocoGt = COCO(gt_json)
    cocoDt = cocoGt.loadRes(result_json)

    scorethr=0.5
    ovthresh=0.3

    catIds = cocoGt.getCatIds()
    #single class
    outputs={}
    mAP=[]

    with Pool(processes=4) as pool:
        args = [(k,catId,cocoGt,cocoDt,scorethr,ovthresh)
                for k, catId in enumerate(catIds)]
        analyze_results = pool.starmap(analyze_individual_category_with_ap, args)

    for k, catId in enumerate(catIds):
        nm = cocoGt.loadCats(catId)[0]
        print(f'--------------saving {k + 1}-{nm["name"]}---------------')
        analyze_result = analyze_results[k]
        outputs[nm["name"]]=analyze_result
        if "ap" in outputs[nm["name"]]:
            ap=outputs[nm["name"]]["ap"]
            mAP.append(ap)
   
    # 单线程
    # for k, catId in enumerate(catIds):
    #     nm = cocoGt.loadCats(catId)[0]
    #     outputs[nm["name"]]=analyze_individual_category_with_ap(k,catId,cocoGt,cocoDt,scorethr,ovthresh)
    #     if "ap" in outputs[nm["name"]]:
    #         ap=outputs[nm["name"]]["ap"]
    #         mAP.append(ap)

    mAP = tuple(mAP)

    print("***************************")
    # 输出总的mAP
    print("mAP :\t {}".format(float(sum(mAP) / len(mAP))))

    print(outputs)
    res = []
    total_tps = 0
    total_fps = 0
    total_fns = 0
    total_gts = 0
    for key in outputs:
        value=outputs[key]
        gts=value['总数']
        if gts==0:
            continue
        tps=value['检出']
        fps=value['误检']
        fns=value["漏检"]
        recall = tps / (tps+fns + 1e-6)
        wujian=fps / (fps + tps + 1e-6)
        ap=0
        if 'ap' in value:
            ap=value['ap']
            total_gts += gts
            total_tps += tps
            total_fps += fps
            total_fns += fns
        item = '{},{},{},{},{},{},{}\n'.format(key, tps+fns, tps, fps, recall, wujian, ap)
        res.append(item)
    with open(f'{filehead}_score{scorethr}_iou{ovthresh}.csv', 'w') as f:
        line_head = "类别名称,类别数,检出数,误检数,检出率,误检率,AP\n"
        f.write(line_head)
        f.write(''.join(res))
        # total_recall=total_tps / (total_tps+total_fns + 1e-6)
        # total_wujian=total_fps / (total_fps + total_tps + 1e-6)
        #使用xray 旧版本计算公式
        total_recall = total_tps / (total_gts + 1e-6)
        total_wujian = total_fps / (total_gts + 1e-6)
        line = '总数,{},{},{},{},{},{}\n'.format(total_tps+total_fns, total_tps, total_fps,
                                                total_recall,
                                                total_wujian, float(sum(mAP) / len(mAP)))
        print(line)
        f.write(line)

if __name__ == '__main__':
    main()