#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Donny You(youansheng@gmail.com)
# ROI sample layer for Detection training.


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import torch
import random

from utils.helpers.det_helper import DetHelper
from utils.tools.logger import Logger as Log


class RoiSampleLayer(object):
    def __init__(self, configer):
        self.configer = configer

    def __call__(self, indices_and_rois, gt_bboxes, gt_bboxes_num, gt_labels):
        n_sample = self.configer.get('roi', 'loss')['n_sample']
        pos_iou_thresh = self.configer.get('roi', 'loss')['pos_iou_thresh']
        neg_iou_thresh_hi = self.configer.get('roi', 'loss')['neg_iou_thresh_hi']
        neg_iou_thresh_lo = self.configer.get('roi', 'loss')['neg_iou_thresh_lo']
        pos_ratio = self.configer.get('roi', 'loss')['pos_ratio']
        loc_normalize_mean = self.configer.get('roi', 'loc_normalize_mean')
        loc_normalize_std = self.configer.get('roi', 'loc_normalize_std')

        sample_roi_list = list()
        gt_roi_loc_list = list()
        gt_roi_label_list= list()

        for i in range(len(gt_bboxes)):
            temp_gt_bboxes = gt_bboxes[i, :gt_bboxes_num[i]].clone()
            temp_gt_labels = gt_labels[i, :gt_bboxes_num[i]].clone()
            input_size = self.configer.get('data', 'input_size')

            print(temp_gt_bboxes)
            for j in range(gt_bboxes_num[i]):
                temp_gt_bboxes[j, 0] = (temp_gt_bboxes[j, 0] * input_size[0]).clamp_(min=0, max=input_size[0]-1)
                temp_gt_bboxes[j, 1] = (temp_gt_bboxes[j, 1] * input_size[1]).clamp_(min=0, max=input_size[1]-1)
                temp_gt_bboxes[j, 2] = (temp_gt_bboxes[j, 2] * input_size[0]).clamp_(min=0, max=input_size[0]-1)
                temp_gt_bboxes[j, 3] = (temp_gt_bboxes[j, 3] * input_size[1]).clamp_(min=0, max=input_size[1]-1)

            print(temp_gt_bboxes)
            
            if temp_gt_bboxes.numel() == 0:
                min_size = self.configer.get('rpn', 'min_size')
                roi_size = random.randint(min_size, min(self.configer.get('data', 'input_size')))
                sample_roi = torch.zeros((1, 4), requires_grad=True).float().to(indices_and_rois.device)
                sample_roi[0, 2:] = roi_size
                gt_roi_loc = torch.zeros((1, 4), requires_grad=True).float().to(sample_roi.device)
                gt_roi_label = torch.ones((1,), requires_grad=True).long().to(sample_roi.device).mul_(-1)

            else:
                pos_roi_per_image = np.round(n_sample * pos_ratio)
                if self.configer.get('phase') == 'debug':
                    rois = indices_and_rois[indices_and_rois[:, 0] == i][:, 1:]
                else:
                    if indices_and_rois.numel() == 0:
                        rois = temp_gt_bboxes
                    else:
                        rois = torch.cat((indices_and_rois[indices_and_rois[:, 0] == i][:, 1:], temp_gt_bboxes), 0)

                iou = DetHelper.bbox_iou(rois, temp_gt_bboxes)
                max_iou, gt_assignment = iou.max(1, keepdim=False)
                # Offset range of classes from [0, n_fg_class - 1] to [1, n_fg_class].
                # The label with value 0 is the background.
                gt_roi_label = temp_gt_labels[gt_assignment] + 1

                max_iou = max_iou.cpu().detach().numpy()
                # Select foreground RoIs as those with >= pos_iou_thresh IoU.
                pos_index = np.where(max_iou >= pos_iou_thresh)[0]
                pos_roi_per_this_image = int(min(pos_roi_per_image, pos_index.size))
                if pos_index.size > 0:
                    pos_index = np.random.choice(pos_index, size=pos_roi_per_this_image, replace=False)

                # Select background RoIs as those within
                # [neg_iou_thresh_lo, neg_iou_thresh_hi).
                neg_index = np.where((max_iou < neg_iou_thresh_hi) & (max_iou >= neg_iou_thresh_lo))[0]
                neg_roi_per_this_image = n_sample - pos_roi_per_this_image
                neg_roi_per_this_image = int(min(neg_roi_per_this_image, neg_index.size))
                if neg_index.size > 0:
                    neg_index = np.random.choice(neg_index, size=neg_roi_per_this_image, replace=False)

                # The indices that we're selecting (both positive and negative).
                keep_index = np.append(pos_index, neg_index)
                gt_roi_label = gt_roi_label[keep_index]
                gt_roi_label[pos_roi_per_this_image:] = 0  # negative labels --> 0
                sample_roi = rois[keep_index]
                # Compute offsets and scales to match sampled RoIs to the GTs.
                boxes = temp_gt_bboxes[gt_assignment][keep_index]
                cxcy = (boxes[:, :2] + boxes[:, 2:]) / 2 - (sample_roi[:, :2] + sample_roi[:, 2:]) / 2  # [8732,2]
                cxcy /= (sample_roi[:, 2:] - sample_roi[:, :2])
                wh = (boxes[:, 2:] - boxes[:, :2]) / (sample_roi[:, 2:] - sample_roi[:, :2])  # [8732,2]
                wh = torch.log(wh)
                loc = torch.cat([cxcy, wh], 1)  # [8732,4]
                # loc = loc[:, [1, 0, 3, 2]]

                normalize_mean = torch.Tensor(loc_normalize_mean).to(loc.device)
                normalize_std = torch.Tensor(loc_normalize_std).to(loc.device)
                gt_roi_loc = (loc - normalize_mean) / normalize_std

            batch_index = i * torch.ones((len(sample_roi),)).to(sample_roi.device)
            sample_roi = torch.cat([batch_index[:, None], sample_roi], dim=1).contiguous()
            sample_roi_list.append(sample_roi)
            gt_roi_loc_list.append(gt_roi_loc)
            gt_roi_label_list.append(gt_roi_label)

        return torch.cat(sample_roi_list, 0), torch.cat(gt_roi_loc_list, 0), torch.cat(gt_roi_label_list, 0)
