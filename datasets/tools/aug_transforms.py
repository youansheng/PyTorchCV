#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Author: Donny You (youansheng@gmail.com)


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import random

import cv2
import matplotlib
import numpy as np
from PIL import Image, ImageFilter, ImageOps

from utils.tools.logger import Logger as Log


class RandomPad(object):
    """ Padding the Image to proper size.
            Args:
                stride: the stride of the network.
                pad_value: the value that pad to the image border.
                img: Image object as input.

            Returns::
                img: Image object.
    """
    def __init__(self, pad_border=None, pad_ratio=0.5):
        assert isinstance(pad_border, int)
        self.pad_border = pad_border
        self.ratio = pad_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)
        if rand_value > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        left_pad = random.randint(-self.pad_border, self.pad_border)  # pad_left
        up_pad = random.randint(-self.pad_border, self.pad_border)  # pad_up
        right_pad = -left_pad  # pad_right
        down_pad = -up_pad  # pad_down

        img = ImageOps.expand(img, (left_pad, up_pad, right_pad, down_pad), fill=(128, 128, 128))

        if labelmap is not None:
            labelmap = ImageOps.expand(labelmap, (left_pad, up_pad, right_pad, down_pad), fill=255)

        if maskmap is not None:
            maskmap = ImageOps.expand(maskmap, (left_pad, up_pad, right_pad, down_pad), fill=1)

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])

            for i in range(num_objects):
                for j in range(num_keypoints):
                    kpts[i][j][0] += left_pad
                    kpts[i][j][1] += up_pad

        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                bboxes[i][0] += left_pad
                bboxes[i][1] += up_pad
                bboxes[i][2] += left_pad
                bboxes[i][3] += up_pad

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomHFlip(object):
    def __init__(self, swap_pair=None, flip_ratio=0.5):
        self.swap_pair = swap_pair
        self.ratio = flip_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)

        if rand_value > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        width, height = img.size
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if labelmap is not None:
            labelmap = labelmap.transpose(Image.FLIP_LEFT_RIGHT)

        if maskmap is not None:
            maskmap = maskmap.transpose(Image.FLIP_LEFT_RIGHT)

        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                xmin = width - 1 - bboxes[i][2]
                xmax = width - 1 - bboxes[i][0]
                bboxes[i][0] = xmin
                bboxes[i][2] = xmax

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])

            for i in range(num_objects):
                for j in range(num_keypoints):
                    kpts[i][j][0] = width - 1 - kpts[i][j][0]

            for pair in self.swap_pair:
                for i in range(num_objects):
                    temp_point = kpts[i][pair[0] - 1]
                    kpts[i][pair[0] - 1] = kpts[i][pair[1] - 1]
                    kpts[i][pair[1] - 1] = temp_point

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomBrightness(object):
    def __init__(self, shift_value=30, brightness_ratio=0.5):
        self.shift_value = shift_value
        self.ratio = brightness_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)
        if rand_value > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        shift = np.random.uniform(-self.shift_value, self.shift_value, size=1)
        image = np.array(img, dtype=float)
        image[:, :, :] += shift
        image = np.around(image)
        image = np.clip(image, 0, 255)
        image = image.astype(np.uint8)
        image = Image.fromarray(image)

        return image, labelmap, maskmap, kpts, bboxes, labels


class RandomGaussBlur(object):
    def __init__(self, max_blur=4, blur_ratio=0.5):
        self.max_blur = max_blur
        self.ratio = blur_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)
        if rand_value > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        blur_value = np.random.uniform(0, self.max_blur)
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_value))
        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomHSV(object):
    """
        Args:
            h_range (float tuple): random ratio of the hue channel,
                new_h range from h_range[0]*old_h to h_range[1]*old_h.
            s_range (float tuple): random ratio of the saturation channel,
                new_s range from s_range[0]*old_s to s_range[1]*old_s.
            v_range (int tuple): random bias of the value channel,
                new_v range from old_v-v_range to old_v+v_range.
        Notice:
            h range: 0-1
            s range: 0-1
            v range: 0-255
    """

    def __init__(self, h_range, s_range, v_range, hsv_ratio=0.5):
        assert isinstance(h_range, (list, tuple)) and \
               isinstance(s_range, (list, tuple)) and \
               isinstance(v_range, (list, tuple))
        self.h_range = h_range
        self.s_range = s_range
        self.v_range = v_range
        self.ratio = hsv_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)
        if rand_value > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        img = np.array(img)
        img_hsv = matplotlib.colors.rgb_to_hsv(img)
        img_h, img_s, img_v = img_hsv[:, :, 0], img_hsv[:, :, 1], img_hsv[:, :, 2]
        h_random = np.random.uniform(min(self.h_range), max(self.h_range))
        s_random = np.random.uniform(min(self.s_range), max(self.s_range))
        v_random = np.random.uniform(min(self.v_range), max(self.v_range))
        img_h = np.clip(img_h * h_random, 0, 1)
        img_s = np.clip(img_s * s_random, 0, 1)
        img_v = np.clip(img_v * v_random, 0, 255)
        img_hsv = np.stack([img_h, img_s, img_v], axis=2)
        img_new = matplotlib.colors.hsv_to_rgb(img_hsv)

        return Image.fromarray(img_new.astype(np.uint8)), labelmap, maskmap, kpts, bboxes, labels


class Resize(object):
    """Resize the given numpy.ndarray to random size and aspect ratio.

    Args:
        scale_min: the min scale to resize.
        scale_max: the max scale to resize.
    """

    def __init__(self, size=None):

        if size is not None:
            if isinstance(size, int):
                self.size = (size, size)
            elif isinstance(size, collections.Iterable) and len(size) == 2:
                self.size = size
            else:
                raise TypeError('Got inappropriate size arg: {}'.format(size))
        else:
            self.size = None

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        """
        Args:
            img     (Image):   Image to be resized.
            maskmap    (Image):   Mask to be resized.
            kpt     (list):    keypoints to be resized.
            center: (list):    center points to be resized.

        Returns:
            Image:  Randomly resize image.
            Image:  Randomly resize maskmap.
            list:   Randomly resize keypoints.
            list:   Randomly resize center points.
        """
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        width, height = img.size
        w_scale_ratio = self.size[0] / width
        h_scale_ratio = self.size[1] / height

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])

            for i in range(num_objects):
                for j in range(num_keypoints):
                    kpts[i][j][0] *= w_scale_ratio
                    kpts[i][j][1] *= h_scale_ratio

        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                bboxes[i][0] *= w_scale_ratio
                bboxes[i][1] *= h_scale_ratio
                bboxes[i][2] *= w_scale_ratio
                bboxes[i][3] *= h_scale_ratio

        img = img.resize(self.size, Image.BILINEAR)
        if labelmap is not None:
            labelmap = labelmap.resize(self.size, Image.NEAREST)
        if maskmap is not None:
            maskmap = maskmap.resize(self.size, Image.CUBIC)

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomResize(object):
    """Resize the given numpy.ndarray to random size and aspect ratio.

    Args:
        scale_min: the min scale to resize.
        scale_max: the max scale to resize.
    """

    def __init__(self, scale_min=0.75, scale_max=1.25, size=None, resize_ratio=0.5):
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.ratio = resize_ratio

        if size is not None:
            if isinstance(size, int):
                self.size = (size, size)
            elif isinstance(size, collections.Iterable) and len(size) == 2:
                self.size = size
            else:
                raise TypeError('Got inappropriate size arg: {}'.format(size))
        else:
            self.size = None

    @staticmethod
    def get_scale(output_size, bboxes):
        scale = 1.0
        if output_size is not None and bboxes is not None and len(bboxes) > 0:
            bboxes = np.array(bboxes)
            border = bboxes[:, 2:] - bboxes[:, 0:2]
            scale = 0.6 / max(max(border[:, 0]) / output_size[0], max(border[:, 1]) / output_size[1])

        return scale

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        """
        Args:
            img     (Image):   Image to be resized.
            maskmap    (Image):   Mask to be resized.
            kpt     (list):    keypoints to be resized.
            center: (list):    center points to be resized.

        Returns:
            Image:  Randomly resize image.
            Image:  Randomly resize maskmap.
            list:   Randomly resize keypoints.
            list:   Randomly resize center points.
        """
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        width, height = img.size
        rand_value = random.randint(1, 100)
        if rand_value <= 100 * self.ratio:
            scale = self.get_scale(self.size, bboxes)
            scale_ratio = random.uniform(self.scale_min, self.scale_max) * scale
        else:
            scale_ratio = 1.0

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])

            for i in range(num_objects):
                for j in range(num_keypoints):
                    kpts[i][j][0] *= scale_ratio
                    kpts[i][j][1] *= scale_ratio

        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                bboxes[i][0] *= scale_ratio
                bboxes[i][1] *= scale_ratio
                bboxes[i][2] *= scale_ratio
                bboxes[i][3] *= scale_ratio

        converted_size = (int(width*scale_ratio), int(height*scale_ratio))

        img = img.resize(converted_size, Image.BILINEAR)
        if labelmap is not None:
            labelmap = labelmap.resize(converted_size, Image.NEAREST)
        if maskmap is not None:
            maskmap = maskmap.resize(converted_size, Image.CUBIC)

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomRotate(object):
    """Rotate the input numpy.ndarray and points to the given degree.

    Args:
        degree (number): Desired rotate degree.
    """

    def __init__(self, max_degree, rotate_ratio=0.5):
        assert isinstance(max_degree, int)
        self.max_degree = max_degree
        self.ratio = rotate_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        """
        Args:
            img    (Image):     Image to be rotated.
            maskmap   (Image):     Mask to be rotated.
            kpt    (list):      Keypoints to be rotated.
            center (list):      Center points to be rotated.

        Returns:
            Image:     Rotated image.
            list:      Rotated key points.
        """
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        rand_value = random.randint(1, 100)
        if rand_value <= 100 * self.ratio:
            rotate_degree = random.uniform(-self.max_degree, self.max_degree)
        else:
            return img, labelmap, maskmap, kpts, bboxes, labels

        img = np.array(img)
        height, width, _ = img.shape

        img_center = (width / 2.0, height / 2.0)

        rotate_mat = cv2.getRotationMatrix2D(img_center, rotate_degree, 1.0)
        cos_val = np.abs(rotate_mat[0, 0])
        sin_val = np.abs(rotate_mat[0, 1])
        new_width = int(height * sin_val + width * cos_val)
        new_height = int(height * cos_val + width * sin_val)
        rotate_mat[0, 2] += (new_width / 2.) - img_center[0]
        rotate_mat[1, 2] += (new_height / 2.) - img_center[1]
        img = cv2.warpAffine(img, rotate_mat, (new_width, new_height), borderValue=(128, 128, 128))
        img = Image.fromarray(img)
        if labelmap is not None:
            labelmap = np.array(labelmap)
            labelmap = cv2.warpAffine(labelmap, rotate_mat, (new_width, new_height),
                                      borderValue=(255, 255, 255), flags=cv2.INTER_NEAREST)
            labelmap = Image.fromarray(labelmap)

        if maskmap is not None:
            maskmap = np.array(maskmap)
            maskmap = cv2.warpAffine(maskmap, rotate_mat, (new_width, new_height), borderValue=(1, 1, 1))
            maskmap = Image.fromarray(maskmap)

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])
            for i in range(num_objects):
                for j in range(num_keypoints):
                    x = kpts[i][j][0]
                    y = kpts[i][j][1]
                    p = np.array([x, y, 1])
                    p = rotate_mat.dot(p)
                    kpts[i][j][0] = p[0]
                    kpts[i][j][1] = p[1]

        # It is not right for object detection tasks.
        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                bbox_temp = [bboxes[i][0], bboxes[i][1], bboxes[i][2], bboxes[i][1],
                             bboxes[i][0], bboxes[i][3], bboxes[i][2], bboxes[i][3]]

                for node in range(4):
                    x = bbox_temp[node * 2]
                    y = bbox_temp[node * 2 + 1]
                    p = np.array([x, y, 1])
                    p = rotate_mat.dot(p)
                    bbox_temp[node * 2] = p[0]
                    bbox_temp[node * 2 + 1] = p[1]

                bboxes[i] = [min(bbox_temp[0], bbox_temp[2], bbox_temp[4], bbox_temp[6]),
                             min(bbox_temp[1], bbox_temp[3], bbox_temp[5], bbox_temp[7]),
                             max(bbox_temp[0], bbox_temp[2], bbox_temp[4], bbox_temp[6]),
                             max(bbox_temp[1], bbox_temp[3], bbox_temp[5], bbox_temp[7])]

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomCrop(object):
    """Crop the given numpy.ndarray and  at a random location.

    Args:
        size (int or tuple): Desired output size of the crop.(w, h)
    """

    def __init__(self, crop_size, crop_ratio=0.5, method='focus', grid=None, center_jitter=None):
        self.ratio = crop_ratio
        self.method = method
        self.grid = grid
        self.center_jitter = center_jitter

        if isinstance(crop_size, float):
            self.size = (crop_size, crop_size)
        elif isinstance(crop_size, collections.Iterable) and len(crop_size) == 2:
            self.size = crop_size
        else:
            raise TypeError('Got inappropriate size arg: {}'.format(crop_size))

    def get_center(self, img_size, bboxes):
        max_center = [img_size[0] / 2, img_size[1] / 2]

        if self.method == 'center':
            return max_center, -1

        elif bboxes is None or len(bboxes) == 0 or self.method == 'random':
            x = random.randint(min(self.size[0] // 2, img_size[0] // 2 - 1),
                               max(img_size[0] - self.size[0] // 2, img_size[0] // 2))
            y = random.randint(min(self.size[1] // 2, img_size[1] // 2 - 1),
                               max(img_size[1] - self.size[1] // 2, img_size[1] // 2))
            return [x, y], -1

        elif self.method == 'focus':
            max_index = 0
            bboxes = np.array(bboxes)
            border = bboxes[:, 2:] - bboxes[:, 0:2]
            for i in range(len(border)):
                if border[i][0] * border[i][1] >= border[max_index][0] * border[max_index][1]:
                    max_index = i
                    max_center = [(bboxes[i][0] + bboxes[i][2]) / 2, (bboxes[i][1] + bboxes[i][3]) / 2]

            if self.center_jitter is not None:
                jitter = random.randint(-self.center_jitter, self.center_jitter)
                max_center[0] += jitter
                jitter = random.randint(-self.center_jitter, self.center_jitter)
                max_center[1] += jitter

            return max_center, max_index

        elif self.method == 'grid':
            grid_x = random.randint(0, self.grid[0] - 1)
            grid_y = random.randint(0, self.grid[1] - 1)
            if img_size[0] - self.size[0] < 0:
                x = img_size[0] // 2
            else:
                x = self.size[0] // 2 + grid_x * ((img_size[0] - self.size[0]) // (self.grid[0] - 1))

            if img_size[1] - self.size[1] < 0:
                y = img_size[1] // 2
            else:
                y = self.size[1] // 2 + grid_y * ((img_size[1] - self.size[1]) // (self.grid[1] - 1))

            return [x, y], -1

        else:
            Log.error('Crop method {} is invalid.'.format(self.method))
            exit(1)

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        """
        Args:
            img (Image):   Image to be cropped.
            maskmap (Image):  Mask to be cropped.
            kpts (list):    keypoints to be cropped.
            bboxes (list): bounding boxes.

        Returns:
            Image:  Cropped image.
            Image:  Cropped maskmap.
            list:   Cropped keypoints.
            list:   Cropped center points.
        """
        assert isinstance(img, Image.Image)
        assert labelmap is None or isinstance(labelmap, Image.Image)
        assert maskmap is None or isinstance(maskmap, Image.Image)

        if random.randint(1, 100) > 100 * self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels

        center, index = self.get_center(img.size, bboxes)

        # img = ImageHelper.draw_box(img, bboxes[index])
        offset_left = int(center[0] - self.size[0] / 2)
        offset_up = int(center[1] - self.size[1] / 2)

        if kpts is not None and len(kpts) > 0:
            num_objects = len(kpts)
            num_keypoints = len(kpts[0])

            for i in range(num_objects):
                for j in range(num_keypoints):
                    kpts[i][j][0] -= offset_left
                    kpts[i][j][1] -= offset_up

        if bboxes is not None and len(bboxes) > 0:
            for i in range(len(bboxes)):
                bboxes[i][0] -= offset_left
                bboxes[i][1] -= offset_up
                bboxes[i][2] -= offset_left
                bboxes[i][3] -= offset_up
                bboxes[i][0] = min(max(0, bboxes[i][0]), self.size[0]-1)
                bboxes[i][1] = min(max(0, bboxes[i][1]), self.size[1]-1)
                bboxes[i][2] = min(max(0, bboxes[i][2]), self.size[0]-1)
                bboxes[i][3] = min(max(0, bboxes[i][3]), self.size[1]-1)

        img = ImageOps.expand(img,
                              border=(-offset_left, -offset_up, self.size[0] + offset_left, self.size[1] + offset_up),
                              fill=(128, 128, 128))
        img = img.crop((0, 0, self.size[0], self.size[1]))

        if maskmap is not None:
            maskmap = ImageOps.expand(maskmap,
                                      border=(-offset_left, -offset_up,
                                              self.size[0] + offset_left, self.size[1] + offset_up), fill=1)
            maskmap = maskmap.crop((0, 0, self.size[0], self.size[1]))

        if labelmap is not None:
            labelmap = ImageOps.expand(labelmap, border=(-offset_left, -offset_up,
                                                         self.size[0] + offset_left,
                                                         self.size[1] + offset_up), fill=255)
            labelmap = labelmap.crop((0, 0, self.size[0], self.size[1]))

        return img, labelmap, maskmap, kpts, bboxes, labels


class RandomDetCrop(object):
    """Crop
    Arguments:
        img (Image): the image being input during training
        boxes (Tensor): the original bounding boxes in pt form
        labels (Tensor): the class labels for each bbox
        mode (float tuple): the min and max jaccard overlaps
    Return:
        (img, boxes, classes)
            img (Image): the cropped image
            boxes (Tensor): the adjusted bounding boxes in pt form
            labels (Tensor): the class labels for each bbox
    """
    def __init__(self):
        self.sample_options = (
            # using entire original input image
            None,
            # sample a patch s.t. MIN jaccard w/ obj in .1,.3,.4,.7,.9
            (0.1, None),
            (0.3, None),
            (0.7, None),
            (0.9, None),
            # randomly sample a patch
            (None, None),
        )

    @staticmethod
    def intersect(box_a, box_b):
        max_xy = np.minimum(box_a[:, 2:], box_b[2:])
        min_xy = np.maximum(box_a[:, :2], box_b[:2])
        inter = np.clip((max_xy - min_xy), a_min=0, a_max=np.inf)
        return inter[:, 0] * inter[:, 1]

    @staticmethod
    def jaccard_numpy(box_a, box_b):
        """Compute the jaccard overlap of two sets of boxes.  The jaccard overlap
            is simply the intersection over union of two boxes.
            E.g.:
                A ∩ B / A ∪ B = A ∩ B / (area(A) + area(B) - A ∩ B)
            Args:
                box_a: Multiple bounding boxes, Shape: [num_boxes,4]
                box_b: Single bounding box, Shape: [4]
            Return:
                jaccard overlap: Shape: [box_a.shape[0], box_a.shape[1]]
            """
        inter = RandomDetCrop.intersect(box_a, box_b)
        area_a = ((box_a[:, 2] - box_a[:, 0]) *
                  (box_a[:, 3] - box_a[:, 1]))  # [A,B]
        area_b = ((box_b[2] - box_b[0]) *
                  (box_b[3] - box_b[1]))  # [A,B]
        union = area_a + area_b - inter
        return inter / union  # [A,B]

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):
        assert labelmap is None and maskmap is None and kpts is None and bboxes is not None

        width, height = img.size

        while True:
            # randomly choose a mode
            mode = random.choice(self.sample_options)
            if mode is None:
                return img, labelmap, maskmap, kpts, bboxes, labels

            min_iou, max_iou = mode
            if min_iou is None:
                min_iou = float('-inf')
            if max_iou is None:
                max_iou = float('inf')

            # max trails (50)
            for _ in range(50):

                w = random.uniform(0.3 * width, width)
                h = random.uniform(0.3 * height, height)

                # aspect ratio constraint b/t .5 & 2
                if h / w < 0.5 or h / w > 2:
                    continue

                left = random.uniform(width - w)
                top = random.uniform(height - h)

                # convert to integer rect x1,y1,x2,y2
                rect = np.array([int(left), int(top), int(left+w), int(top+h)])

                # calculate IoU (jaccard overlap) b/t the cropped and gt boxes
                overlap = self.jaccard_numpy(bboxes, rect)

                # is min and max overlap constraint satisfied? if not try again
                if overlap.min() < min_iou and max_iou < overlap.max():
                    continue

                # cut the crop from the image
                current_img = img.crop((rect[0], rect[1], rect[2], rect[3]))

                # keep overlap with gt box IF center in sampled patch
                centers = (bboxes[:, :2] + bboxes[:, 2:]) / 2.0

                # mask in all gt boxes that above and to the left of centers
                m1 = (rect[0] < centers[:, 0]) * (rect[1] < centers[:, 1])

                # mask in all gt boxes that under and to the right of centers
                m2 = (rect[2] > centers[:, 0]) * (rect[3] > centers[:, 1])

                # mask in that both m1 and m2 are true
                mask = m1 * m2

                # have any valid boxes? try again if not
                if not mask.any():
                    continue

                # take only matching gt boxes
                current_boxes = bboxes[mask, :].copy()

                # take only matching gt labels
                current_labels = labels[mask]

                # should we use the box left and top corner or the crop's
                current_boxes[:, :2] = np.maximum(current_boxes[:, :2],
                                                  rect[:2])
                # adjust to crop (by substracting crop's left,top)
                current_boxes[:, :2] -= rect[:2]

                current_boxes[:, 2:] = np.minimum(current_boxes[:, 2:],
                                                  rect[2:])
                # adjust to crop (by substracting crop's left,top)
                current_boxes[:, 2:] -= rect[:2]

                return current_img, labelmap, maskmap, kpts, current_boxes.tolist(), current_labels.tolist()


class AugCompose(object):
    """Composes several transforms together.

    Args:
        transforms (list of ``Transform`` objects): list of transforms to compose.

    Example:
        >>> AugCompose([
        >>>     RandomCrop(),
        >>> ])
    """

    def __init__(self, configer, split='train'):
        self.configer = configer
        self.split = split

        if split == 'train':
            self.transforms = {
                'random_pad': RandomPad(
                    pad_border=self.configer.get('trans_params', 'random_pad')['pad_border'],
                    pad_ratio=self.configer.get('train_trans', 'pad_ratio')
                ),
                'random_brightness': RandomBrightness(
                    shift_value=self.configer.get('trans_params', 'random_brightness')['shift_value'],
                    brightness_ratio=self.configer.get('train_trans', 'brightness_ratio')
                ),
                'random_gauss_blur': RandomGaussBlur(
                    max_blur=self.configer.get('trans_params', 'random_gauss_blur')['max_blur'],
                    blur_ratio=self.configer.get('train_trans', 'blur_ratio')
                ),
                'random_hsv': RandomHSV(
                    h_range=self.configer.get('trans_params', 'random_hsv')['h_range'],
                    s_range=self.configer.get('trans_params', 'random_hsv')['s_range'],
                    v_range=self.configer.get('trans_params', 'random_hsv')['v_range'],
                    hsv_ratio=self.configer.get('train_trans', 'hsv_ratio')
                ),
                'random_hflip': RandomHFlip(
                    swap_pair=self.configer.get('trans_params', 'random_hflip')['swap_pair'],
                    flip_ratio=self.configer.get('train_trans', 'flip_ratio')
                ),
                'random_resize': RandomResize(
                    scale_min=self.configer.get('trans_params', 'random_resize')['scale_min'],
                    scale_max=self.configer.get('trans_params', 'random_resize')['scale_max'],
                    size=self.configer.get('data', 'train_input_size'),
                    resize_ratio=self.configer.get('train_trans', 'resize_ratio')
                ),
                'random_rotate': RandomRotate(
                    max_degree=self.configer.get('trans_params', 'random_rotate')['rotate_degree'],
                    rotate_ratio=self.configer.get('train_trans', 'rotate_ratio')
                ),
                'random_crop': RandomCrop(
                    crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                    method=self.configer.get('trans_params', 'random_crop')['method'],
                    grid=self.configer.get('trans_params', 'random_crop')['grid'],
                    center_jitter=self.configer.get('trans_params', 'random_crop')['center_jitter'],
                    crop_ratio=self.configer.get('train_trans', 'crop_ratio')
                ),
                'resize': Resize(size=self.configer.get('data', 'train_input_size')),
            }
        else:
            self.transforms = {
                'random_pad': RandomPad(
                    pad_border=self.configer.get('trans_params', 'random_pad')['pad_border'],
                    pad_ratio=self.configer.get('val_trans', 'pad_ratio')
                ),
                'random_brightness': RandomBrightness(
                    shift_value=self.configer.get('trans_params', 'random_brightness')['shift_value'],
                    brightness_ratio=self.configer.get('val_trans', 'brightness_ratio')
                ),
                'random_gauss_blur': RandomGaussBlur(
                    max_blur=self.configer.get('trans_params', 'random_gauss_blur')['max_blur'],
                    blur_ratio=self.configer.get('val_trans', 'blur_ratio')
                ),
                'random_hsv': RandomHSV(
                    h_range=self.configer.get('trans_params', 'random_hsv')['h_range'],
                    s_range=self.configer.get('trans_params', 'random_hsv')['s_range'],
                    v_range=self.configer.get('trans_params', 'random_hsv')['v_range'],
                    hsv_ratio=self.configer.get('val_trans', 'hsv_ratio')
                ),
                'random_hflip': RandomHFlip(
                    swap_pair=self.configer.get('trans_params', 'random_hflip')['swap_pair'],
                    flip_ratio=self.configer.get('val_trans', 'flip_ratio')
                ),
                'random_resize': RandomResize(
                    scale_min=self.configer.get('trans_params', 'random_resize')['scale_min'],
                    scale_max=self.configer.get('trans_params', 'random_resize')['scale_max'],
                    size=self.configer.get('data', 'val_input_size'),
                    resize_ratio=self.configer.get('val_trans', 'resize_ratio')
                ),
                'random_rotate': RandomRotate(
                    max_degree=self.configer.get('trans_params', 'random_rotate')['rotate_degree'],
                    rotate_ratio=self.configer.get('val_trans', 'rotate_ratio')
                ),
                'random_crop': RandomCrop(
                    crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                    method=self.configer.get('trans_params', 'random_crop')['method'],
                    grid=self.configer.get('trans_params', 'random_crop')['grid'],
                    center_jitter=self.configer.get('trans_params', 'random_crop')['center_jitter'],
                    crop_ratio=self.configer.get('val_trans', 'crop_ratio')
                ),
                'resize': Resize(size=self.configer.get('data', 'val_input_size')),
            }

    def __check_none(self, key_list, value_list):
        for key, value in zip(key_list, value_list):
            if value == 'y' and key is None:
                return False

            if value == 'n' and key is not None:
                return False

        return True

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None):

        if self.split == 'train':
            for trans_key in self.configer.get('train_trans', 'trans_seq'):
                (img, labelmap, maskmap,
                 kpts, bboxes, labels) = self.transforms[trans_key](img, labelmap, maskmap, kpts, bboxes, labels)

        else:
            for trans_key in self.configer.get('val_trans', 'trans_seq'):
                (img, labelmap, maskmap,
                 kpts, bboxes, labels) = self.transforms[trans_key](img, labelmap, maskmap, kpts, bboxes, labels)

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'n', 'n', 'n', 'n']):
            return img

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['y', 'n', 'n', 'n', 'n']):
            return img, labelmap

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'n', 'n', 'y', 'n']):
            return img, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'n', 'y', 'n', 'n']):
            return img, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'n', 'y', 'y', 'n']):
            return img, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'y', 'y', 'n', 'n']):
            return img, maskmap, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['y', 'y', 'y', 'n', 'n']):
            return img, labelmap, maskmap, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'y', 'y', 'y', 'n']):
            return img, maskmap, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['y', 'y', 'y', 'y', 'n']):
            return img, labelmap, maskmap, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels], ['n', 'n', 'n', 'y', 'y']):
            return img, bboxes, labels

        Log.error('Params is not valid.')
        exit(1)
