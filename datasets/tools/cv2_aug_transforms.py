#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Donny You (youansheng@gmail.com)


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import random
import math
import cv2
import numpy as np

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

    def __init__(self, up_scale_range=None, pad_ratio=0.5, mean=(104, 117, 123)):
        # do something
        assert isinstance(up_scale_range, (list, tuple))
        self.up_scale_range = up_scale_range
        self.ratio = pad_ratio
        self.mean = mean

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, channels = img.shape
        expand_ratio = random.uniform(self.up_scale_range[0], self.up_scale_range[1])
        pad_ratio = expand_ratio - 1.0
        pad_width = int(pad_ratio * width)
        pad_height = int(pad_ratio * height)

        left_pad = random.randint(0, pad_width)  # pad_left
        up_pad = random.randint(0, pad_height)  # pad_up

        expand_image = np.zeros((int(height * expand_ratio), int(width * expand_ratio), channels), dtype=img.dtype)
        expand_image[:, :, :] = self.mean
        expand_image[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)] = img
        img = expand_image

        if labelmap is not None:
            expand_labelmap = np.zeros((int(height * expand_ratio), int(width * expand_ratio)), dtype=labelmap.dtype)
            expand_labelmap[:, :] = 255
            expand_labelmap[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)] = labelmap
            labelmap = expand_labelmap

        if maskmap is not None:
            expand_maskmap = np.zeros((int(height * expand_ratio), int(width * expand_ratio)), dtype=maskmap.dtype)
            expand_maskmap[:, :] = 1
            expand_maskmap[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)] = maskmap
            maskmap = expand_maskmap

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    polygons[object_id][polygon_id][0::2] += left_pad
                    polygons[object_id][polygon_id][1::2] += up_pad

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] += left_pad
            kpts[:, :, 1] += up_pad

        if bboxes is not None and bboxes.size > 0:
            bboxes[:, 0::2] += left_pad
            bboxes[:, 1::2] += up_pad

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomShift(object):
    """ Padding the Image to proper size.
            Args:
                stride: the stride of the network.
                pad_value: the value that pad to the image border.
                img: Image object as input.
            Returns::
                img: Image object.
    """

    def __init__(self, shift_pixel=None, shift_ratio=0.5, mean=(104, 117, 123)):
        assert isinstance(shift_pixel, int)
        self.shift_pixel = int(shift_pixel)
        self.ratio = shift_ratio
        self.mean = mean

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, channels = img.shape
        left_pad = random.randint(0, self.shift_pixel * 2)  # pad_left
        up_pad = random.randint(0, self.shift_pixel * 2)  # pad_up

        expand_image = np.zeros((height + self.shift_pixel * 2,
                                 width + self.shift_pixel * 2, channels), dtype=img.dtype)
        expand_image[:, :, :] = self.mean
        expand_image[self.shift_pixel:self.shift_pixel + height, self.shift_pixel:self.shift_pixel + width] = img
        img = expand_image[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)]

        if labelmap is not None:
            expand_labelmap = np.zeros((height + self.shift_pixel * 2,
                                        width + self.shift_pixel * 2), dtype=labelmap.dtype)
            expand_labelmap[:, :] = 255
            expand_labelmap[self.shift_pixel:self.shift_pixel + height,
                            self.shift_pixel:self.shift_pixel + width] = labelmap
            labelmap = expand_labelmap[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)]

        if maskmap is not None:
            expand_maskmap = np.zeros((height + self.shift_pixel * 2,
                                       width + self.shift_pixel * 2), dtype=maskmap.dtype)
            expand_maskmap[:, :] = 1
            expand_maskmap[self.shift_pixel:self.shift_pixel + height,
                           self.shift_pixel:self.shift_pixel + width] = maskmap
            maskmap = expand_maskmap[int(up_pad):int(up_pad + height), int(left_pad):int(left_pad + width)]

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    polygons[object_id][polygon_id][0::2] += (self.shift_pixel - left_pad)
                    polygons[object_id][polygon_id][1::2] += (self.shift_pixel - up_pad)

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] += (self.shift_pixel - left_pad)
            kpts[:, :, 1] += (self.shift_pixel - up_pad)

        if bboxes is not None and bboxes.size > 0:
            bboxes[:, 0::2] += (self.shift_pixel - left_pad)
            bboxes[:, 1::2] += (self.shift_pixel - up_pad)

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomHFlip(object):
    def __init__(self, swap_pair=None, flip_ratio=0.5):
        self.swap_pair = swap_pair
        self.ratio = flip_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, _ = img.shape
        img = cv2.flip(img, 1)
        if labelmap is not None:
            labelmap = cv2.flip(labelmap, 1)

        if maskmap is not None:
            maskmap = cv2.flip(maskmap, 1)

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    polygons[object_id][polygon_id][0::2] = width - 1 - polygons[object_id][polygon_id][0::2]

        if bboxes is not None and bboxes.size > 0:
            xmin = width - 1 - bboxes[:, 2]
            xmax = width - 1 - bboxes[:, 0]
            bboxes[:, 0] = xmin
            bboxes[:, 2] = xmax

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] = width - 1 - kpts[:, :, 0]

            for pair in self.swap_pair:
                temp_point = np.copy(kpts[:, pair[0] - 1])
                kpts[:, pair[0] - 1] = kpts[:, pair[1] - 1]
                kpts[:, pair[1] - 1] = temp_point

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomSaturation(object):
    def __init__(self, lower=0.5, upper=1.5, saturation_ratio=0.5):
        self.lower = lower
        self.upper = upper
        self.ratio = saturation_ratio
        assert self.upper >= self.lower, "saturation upper must be >= lower."
        assert self.lower >= 0, "saturation lower must be non-negative."

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        img = img.astype(np.float32)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img[:, :, 1] *= random.uniform(self.lower, self.upper)
        img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        img = np.clip(img, 0, 255).astype(np.uint8)
        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomHue(object):
    def __init__(self, delta=18, hue_ratio=0.5):
        assert 0 <= delta <= 360
        self.delta = delta
        self.ratio = hue_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        img = img.astype(np.float32)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img[:, :, 0] += random.uniform(-self.delta, self.delta)
        img[:, :, 0][img[:, :, 0] > 360] -= 360
        img[:, :, 0][img[:, :, 0] < 0] += 360
        img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        img = np.clip(img, 0, 255).astype(np.uint8)
        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomPerm(object):
    def __init__(self, perm_ratio=0.5):
        self.ratio = perm_ratio
        self.perms = ((0, 1, 2), (0, 2, 1),
                      (1, 0, 2), (1, 2, 0),
                      (2, 0, 1), (2, 1, 0))

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        swap = self.perms[random.randint(0, len(self.perms) - 1)]
        img = img[:, :, swap].astype(np.uint8)
        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomContrast(object):
    def __init__(self, lower=0.5, upper=1.5, contrast_ratio=0.5):
        self.lower = lower
        self.upper = upper
        self.ratio = contrast_ratio
        assert self.upper >= self.lower, "contrast upper must be >= lower."
        assert self.lower >= 0, "contrast lower must be non-negative."

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        img = img.astype(np.float32)
        img *= random.uniform(self.lower, self.upper)
        img = np.clip(img, 0, 255).astype(np.uint8)

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomBrightness(object):
    def __init__(self, shift_value=30, brightness_ratio=0.5):
        self.shift_value = shift_value
        self.ratio = brightness_ratio

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        img = img.astype(np.float32)
        shift = random.randint(-self.shift_value, self.shift_value)
        img[:, :, :] += shift
        img = np.around(img)
        img = np.clip(img, 0, 255).astype(np.uint8)

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomResize(object):
    """Resize the given numpy.ndarray to random size and aspect ratio.

    Args:
        scale_min: the min scale to resize.
        scale_max: the max scale to resize.
    """

    def __init__(self, scale_range=(0.75, 1.25), target_size=None,
                 resize_bound=None, method='random', resize_ratio=0.5):
        self.scale_range = scale_range
        self.resize_bound = resize_bound
        self.method = method
        self.ratio = resize_ratio

        if target_size is not None:
            if isinstance(target_size, int):
                self.input_size = (target_size, target_size)
            elif isinstance(target_size, (list, tuple)) and len(target_size) == 2:
                self.input_size = target_size
            else:
                raise TypeError('Got inappropriate size arg: {}'.format(target_size))
        else:
            self.input_size = None

    def get_scale(self, img_size, bboxes):
        if self.method == 'random':
            scale_ratio = random.uniform(self.scale_range[0], self.scale_range[1])
            return scale_ratio

        elif self.method == 'focus':
            if self.input_size is not None and bboxes is not None and len(bboxes) > 0:
                bboxes = np.array(bboxes)
                border = bboxes[:, 2:] - bboxes[:, 0:2]
                scale = 0.6 / max(max(border[:, 0]) / self.input_size[0], max(border[:, 1]) / self.input_size[1])
                scale_ratio = random.uniform(self.scale_range[0], self.scale_range[1]) * scale
                return scale_ratio

            else:
                scale_ratio = random.uniform(self.scale_range[0], self.scale_range[1])
                return scale_ratio

        elif self.method == 'bound':
            scale1 = self.resize_bound[0] / min(img_size)
            scale2 = self.resize_bound[1] / max(img_size)
            scale = min(scale1, scale2)
            return scale

        else:
            Log.error('Resize method {} is invalid.'.format(self.method))
            exit(1)

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
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
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        height, width, _ = img.shape
        if random.random() < self.ratio:
            scale_ratio = self.get_scale([width, height], bboxes)
        else:
            scale_ratio = 1.0

        if kpts is not None and kpts.size > 0:
            kpts[:, :, :2] *= scale_ratio

        if bboxes is not None and bboxes.size > 0:
            bboxes *= scale_ratio

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    polygons[object_id][polygon_id] *= scale_ratio

        converted_size = (int(width * scale_ratio), int(height * scale_ratio))

        img = cv2.resize(img, converted_size, interpolation=cv2.INTER_CUBIC).astype(np.uint8)
        if labelmap is not None:
            labelmap = cv2.resize(labelmap, converted_size, interpolation=cv2.INTER_NEAREST)

        if maskmap is not None:
            maskmap = cv2.resize(maskmap, converted_size, interpolation=cv2.INTER_NEAREST)

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomRotate(object):
    """Rotate the input numpy.ndarray and points to the given degree.

    Args:
        degree (number): Desired rotate degree.
    """

    def __init__(self, max_degree, rotate_ratio=0.5, mean=(104, 117, 123)):
        assert isinstance(max_degree, int)
        self.max_degree = max_degree
        self.ratio = rotate_ratio
        self.mean = mean

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
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
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() < self.ratio:
            rotate_degree = random.uniform(-self.max_degree, self.max_degree)
        else:
            return img, labelmap, maskmap, kpts, bboxes, labels

        height, width, _ = img.shape

        img_center = (width / 2.0, height / 2.0)

        rotate_mat = cv2.getRotationMatrix2D(img_center, rotate_degree, 1.0)
        cos_val = np.abs(rotate_mat[0, 0])
        sin_val = np.abs(rotate_mat[0, 1])
        new_width = int(height * sin_val + width * cos_val)
        new_height = int(height * cos_val + width * sin_val)
        rotate_mat[0, 2] += (new_width / 2.) - img_center[0]
        rotate_mat[1, 2] += (new_height / 2.) - img_center[1]
        img = cv2.warpAffine(img, rotate_mat, (new_width, new_height), borderValue=self.mean).astype(np.uint8)
        if labelmap is not None:
            labelmap = cv2.warpAffine(labelmap, rotate_mat, (new_width, new_height),
                                      borderValue=(255, 255, 255), flags=cv2.INTER_NEAREST)
            labelmap = labelmap.astype(np.uint8)

        if maskmap is not None:
            maskmap = cv2.warpAffine(maskmap, rotate_mat, (new_width, new_height),
                                     borderValue=(1, 1, 1), flags=cv2.INTER_NEAREST)
            maskmap = maskmap.astype(np.uint8)

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    for i in range(len(polygons[object_id][polygon_id]) // 2):
                        x = polygons[object_id][polygon_id][i * 2]
                        y = polygons[object_id][polygon_id][i * 2 + 1]
                        p = np.array([x, y, 1])
                        p = rotate_mat.dot(p)
                        polygons[object_id][polygon_id][i * 2] = p[0]
                        polygons[object_id][polygon_id][i * 2 + 1] = p[1]

        if kpts is not None and kpts.size > 0:
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
        if bboxes is not None and bboxes.size > 0:
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

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomCrop(object):
    """Crop the given numpy.ndarray and  at a random location.

    Args:
        size (int or tuple): Desired output size of the crop.(w, h)
    """

    def __init__(self, crop_size, crop_ratio=0.5, method='random', grid=None, allow_outside_center=True):
        self.ratio = crop_ratio
        self.method = method
        self.grid = grid
        self.allow_outside_center = allow_outside_center

        if isinstance(crop_size, float):
            self.size = (crop_size, crop_size)
        elif isinstance(crop_size, collections.Iterable) and len(crop_size) == 2:
            self.size = crop_size
        else:
            raise TypeError('Got inappropriate size arg: {}'.format(crop_size))

    def get_center(self, img_size):
        max_center = [img_size[0] // 2, img_size[1] // 2]

        if self.method == 'center':
            return max_center, -1

        elif self.method == 'random':
            if img_size[0] > self.size[0]:
                x = random.randint(self.size[0] // 2, img_size[0] - self.size[0] // 2)
            else:
                x = img_size[0] // 2

            if img_size[1] > self.size[1]:
                y = random.randint(self.size[1] // 2, img_size[1] - self.size[1] // 2)
            else:
                y = img_size[1] // 2

            return [x, y], -1

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

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        """
        Args:
            img (Image):   Image to be cropped.
            maskmap (Image):  Mask to be cropped.

        Returns:
            Image:  Cropped image.
            Image:  Cropped maskmap.
            list:   Cropped keypoints.
            list:   Cropped center points.
        """
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, _ = img.shape
        target_size = [min(self.size[0], width), min(self.size[1], height)]

        center, index = self.get_center([width, height])

        # img = ImageHelper.draw_box(img, bboxes[index])
        offset_left = center[0] - target_size[0] // 2
        offset_up = center[1] - target_size[1] // 2

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] -= offset_left
            kpts[:, :, 1] -= offset_up

        if bboxes is not None and bboxes.size > 0:
            if self.allow_outside_center:
                mask = np.ones(bboxes.shape[0], dtype=bool)
            else:
                crop_bb = np.array([offset_left, offset_up, offset_left + target_size[0], offset_up + target_size[1]])
                center = (bboxes[:, :2] + bboxes[:, 2:]) / 2
                mask = np.logical_and(crop_bb[:2] <= center, center < crop_bb[2:]).all(axis=1)

            bboxes[:, 0::2] -= offset_left
            bboxes[:, 1::2] -= offset_up
            bboxes[:, 0::2] = np.clip(bboxes[:, 0::2], 0, target_size[0] - 1)
            bboxes[:, 1::2] = np.clip(bboxes[:, 1::2], 0, target_size[1] - 1)

            mask = np.logical_and(mask, (bboxes[:, :2] < bboxes[:, 2:]).all(axis=1))
            bboxes = bboxes[mask]
            if labels is not None:
                labels = labels[mask]

            if polygons is not None:
                new_polygons = list()
                for object_id in range(len(polygons)):
                    if mask[object_id] == 1:
                        for polygon_id in range(len(polygons[object_id])):

                            polygons[object_id][polygon_id][0::2] -= offset_left
                            polygons[object_id][polygon_id][1::2] -= offset_up
                            polygons[object_id][polygon_id][0::2] = np.clip(polygons[object_id][polygon_id][0::2],
                                                                            0, target_size[0] - 1)
                            polygons[object_id][polygon_id][1::2] = np.clip(polygons[object_id][polygon_id][1::2],
                                                                            0, target_size[1] - 1)

                        new_polygons.append(polygons[object_id])

                polygons = new_polygons

        img = img[offset_up:offset_up + target_size[1], offset_left:offset_left + target_size[0]]
        if maskmap is not None:
            maskmap = maskmap[offset_up:offset_up + target_size[1], offset_left:offset_left + target_size[0]]

        if labelmap is not None:
            labelmap = labelmap[offset_up:offset_up + target_size[1], offset_left:offset_left + target_size[0]]

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class RandomFocusCrop(object):
    """Crop the given numpy.ndarray and  at a random location.

    Args:
        size (int or tuple): Desired output size of the crop.(w, h)
    """

    def __init__(self, crop_size, crop_ratio=0.5, center_jitter=None, mean=(104, 117, 123), allow_outside_center=True):
        self.ratio = crop_ratio
        self.center_jitter = center_jitter
        self.mean = mean
        self.allow_outside_center = allow_outside_center

        if isinstance(crop_size, float):
            self.size = (crop_size, crop_size)
        elif isinstance(crop_size, collections.Iterable) and len(crop_size) == 2:
            self.size = crop_size
        else:
            raise TypeError('Got inappropriate size arg: {}'.format(crop_size))

    def get_center(self, img_size, bboxes):
        max_center = [img_size[0] // 2, img_size[1] // 2]

        if bboxes is None or len(bboxes) == 0:
            if img_size[0] > self.size[0]:
                x = random.randint(self.size[0] // 2, img_size[0] - self.size[0] // 2)
            else:
                x = img_size[0] // 2

            if img_size[1] > self.size[1]:
                y = random.randint(self.size[1] // 2, img_size[1] - self.size[1] // 2)
            else:
                y = img_size[1] // 2

            return [x, y], -1

        else:
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

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        """
        Args:
            img (Image):   Image to be cropped.
            maskmap (Image):  Mask to be cropped.

        Returns:
            Image:  Cropped image.
            Image:  Cropped maskmap.
            list:   Cropped keypoints.
            list:   Cropped center points.
        """
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, channels = img.shape

        center, index = self.get_center([width, height], bboxes)

        # img = ImageHelper.draw_box(img, bboxes[index])
        offset_left = int(center[0] - self.size[0] // 2)
        offset_up = int(center[1] - self.size[1] // 2)

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] -= offset_left
            kpts[:, :, 1] -= offset_up

        if bboxes is not None and bboxes.size > 0:
            if self.allow_outside_center:
                mask = np.ones(bboxes.shape[0], dtype=bool)
            else:
                crop_bb = np.array([offset_left, offset_up, offset_left + self.size[0], offset_up + self.size[1]])
                center = (bboxes[:, :2] + bboxes[:, 2:]) / 2
                mask = np.logical_and(crop_bb[:2] <= center, center < crop_bb[2:]).all(axis=1)

            bboxes[:, 0::2] -= offset_left
            bboxes[:, 1::2] -= offset_up
            bboxes[:, 0::2] = np.clip(bboxes[:, 0::2], 0, self.size[0] - 1)
            bboxes[:, 1::2] = np.clip(bboxes[:, 1::2], 0, self.size[1] - 1)

            mask = np.logical_and(mask, (bboxes[:, :2] < bboxes[:, 2:]).all(axis=1))
            bboxes = bboxes[mask]
            if labels is not None:
                labels = labels[mask]

            if polygons is not None:
                new_polygons = list()
                for object_id in range(len(polygons)):
                    if mask[object_id] == 1:
                        for polygon_id in range(len(polygons[object_id])):
                            polygons[object_id][polygon_id][0::2] -= offset_left
                            polygons[object_id][polygon_id][1::2] -= offset_up
                            polygons[object_id][polygon_id][0::2] = np.clip(polygons[object_id][polygon_id][0::2],
                                                                            0, self.size[0] - 1)
                            polygons[object_id][polygon_id][1::2] = np.clip(polygons[object_id][polygon_id][1::2],
                                                                            0, self.size[1] - 1)

                        new_polygons.append(polygons[object_id])

                polygons = new_polygons

        expand_image = np.zeros((max(height, self.size[1]) + abs(offset_up),
                                 max(width, self.size[0]) + abs(offset_left), channels), dtype=img.dtype)
        expand_image[:, :, :] = self.mean
        expand_image[abs(min(offset_up, 0)):abs(min(offset_up, 0)) + height,
                     abs(min(offset_left, 0)):abs(min(offset_left, 0)) + width] = img
        img = expand_image[max(offset_up, 0):max(offset_up, 0) + self.size[1],
                           max(offset_left, 0):max(offset_left, 0) + self.size[0]]

        if maskmap is not None:
            expand_maskmap = np.zeros((max(height, self.size[1]) + abs(offset_up),
                                       max(width, self.size[0]) + abs(offset_left)), dtype=maskmap.dtype)
            expand_maskmap[:, :, :] = 1
            expand_maskmap[abs(min(offset_up, 0)):abs(min(offset_up, 0)) + height,
                           abs(min(offset_left, 0)):abs(min(offset_left, 0)) + width] = maskmap
            maskmap = expand_maskmap[max(offset_up, 0):max(offset_up, 0) + self.size[1],
                                     max(offset_left, 0):max(offset_left, 0) + self.size[0]]

        if labelmap is not None:
            expand_labelmap = np.zeros((max(height, self.size[1]) + abs(offset_up),
                                        max(width, self.size[0]) + abs(offset_left)), dtype=labelmap.dtype)
            expand_labelmap[:, :, :] = 255
            expand_labelmap[abs(min(offset_up, 0)):abs(min(offset_up, 0)) + height,
                            abs(min(offset_left, 0)):abs(min(offset_left, 0)) + width] = labelmap
            labelmap = expand_labelmap[max(offset_up, 0):max(offset_up, 0) + self.size[1],
                                       max(offset_left, 0):max(offset_left, 0) + self.size[0]]

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


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

    def __init__(self, det_crop_ratio=0.5, allow_outside_center=True):
        self.ratio = det_crop_ratio
        self.allow_outside_center = allow_outside_center
        self.sample_options = (
            # using entire original input image
            None,
            # sample a patch s.t. MIN jaccard w/ obj in .1,.3,.4,.7,.9
            (0.1, None),
            (0.3, None),
            (0.5, None),
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

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert labelmap is None and maskmap is None and kpts is None and polygons is None
        assert bboxes is not None and labels is not None

        if random.random() > self.ratio:
            return img, labelmap, maskmap, kpts, bboxes, labels, polygons

        height, width, _ = img.shape

        while True:
            # randomly choose a mode
            mode = random.choice(self.sample_options)
            if mode is None:
                return img, labelmap, maskmap, kpts, bboxes, labels, polygons

            min_iou, max_iou = mode
            if min_iou is None:
                min_iou = float('-inf')
            if max_iou is None:
                max_iou = float('inf')

            # max trails (50)
            for _ in range(50):
                scale = random.uniform(0.3, 1.)
                min_ratio = max(0.5, scale * scale)
                max_ratio = min(2.0, 1. / scale / scale)
                ratio = math.sqrt(random.uniform(min_ratio, max_ratio))
                w = int(scale * ratio * width)
                h = int((scale / ratio) * height)

                left = random.randint(0, width - w)
                top = random.randint(0, height - h)

                # convert to integer rect x1,y1,x2,y2
                rect = np.array([int(left), int(top), int(left + w), int(top + h)])

                # calculate IoU (jaccard overlap) b/t the cropped and gt boxes
                overlap = self.jaccard_numpy(bboxes, rect)

                # is min and max overlap constraint satisfied? if not try again
                if overlap.min() < min_iou or max_iou < overlap.max():
                    continue

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


                # cut the crop from the image
                current_img = img[rect[1]:rect[3], rect[0]:rect[2], :]

                # take only matching gt labels
                current_labels = labels[mask]

                # should we use the box left and top corner or the crop's
                current_boxes[:, :2] = np.maximum(current_boxes[:, :2], rect[:2])
                # adjust to crop (by substracting crop's left,top)
                current_boxes[:, :2] -= rect[:2]

                current_boxes[:, 2:] = np.minimum(current_boxes[:, 2:], rect[2:])
                # adjust to crop (by substracting crop's left,top)
                current_boxes[:, 2:] -= rect[:2]

                return current_img, labelmap, maskmap, kpts, current_boxes, current_labels, polygons


class Resize(object):
    """Resize the given numpy.ndarray to random size and aspect ratio.
    Args:
        scale_min: the min scale to resize.
        scale_max: the max scale to resize.
    """

    def __init__(self, target_size=None):
        self.target_size = target_size

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):
        assert isinstance(img, np.ndarray)
        assert labelmap is None or isinstance(labelmap, np.ndarray)
        assert maskmap is None or isinstance(maskmap, np.ndarray)

        height, width, channels = img.shape
        target_width, target_height = self.target_size

        w_scale_ratio = target_width / width
        h_scale_ratio = target_height / height

        if kpts is not None and kpts.size > 0:
            kpts[:, :, 0] *= w_scale_ratio
            kpts[:, :, 1] *= h_scale_ratio

        if bboxes is not None and bboxes.size > 0:
            bboxes[:, 0::2] *= w_scale_ratio
            bboxes[:, 1::2] *= h_scale_ratio

        if polygons is not None:
            for object_id in range(len(polygons)):
                for polygon_id in range(len(polygons[object_id])):
                    polygons[object_id][polygon_id][0::2] *= w_scale_ratio
                    polygons[object_id][polygon_id][1::2] *= h_scale_ratio

        img = cv2.resize(img, self.target_size, interpolation=cv2.INTER_CUBIC)
        if labelmap is not None:
            labelmap = cv2.resize(labelmap, self.target_size, interpolation=cv2.INTER_NEAREST)

        if maskmap is not None:
            maskmap = cv2.resize(maskmap, self.target_size, interpolation=cv2.INTER_NEAREST)

        return img, labelmap, maskmap, kpts, bboxes, labels, polygons


class CV2AugCompose(object):
    """Composes several transforms together.

    Args:
        transforms (list of ``Transform`` objects): list of transforms to compose.

    Example:
        >>> CV2AugCompose([
        >>>     RandomCrop(),
        >>> ])
    """

    def __init__(self, configer, split='train'):
        self.configer = configer
        self.split = split

        self.transforms = dict()
        if self.split == 'train':
            shuffle_train_trans = []
            if not self.configer.is_empty('train_trans', 'shuffle_trans_seq'):
                if isinstance(self.configer.get('train_trans', 'shuffle_trans_seq')[0], list):
                    train_trans_seq_list = self.configer.get('train_trans', 'shuffle_trans_seq')
                    for train_trans_seq in train_trans_seq_list:
                        shuffle_train_trans += train_trans_seq

                else:
                    shuffle_train_trans = self.configer.get('train_trans', 'shuffle_trans_seq')

            if 'random_saturation' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_saturation'] = RandomSaturation(
                    lower=self.configer.get('trans_params', 'random_saturation')['lower'],
                    upper=self.configer.get('trans_params', 'random_saturation')['upper'],
                    saturation_ratio=self.configer.get('train_trans', 'saturation_ratio')
                )

            if 'random_hue' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_hue'] = RandomHue(
                    delta=self.configer.get('trans_params', 'random_hue')['delta'],
                    hue_ratio=self.configer.get('train_trans', 'hue_ratio')
                )

            if 'random_perm' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_perm'] = RandomPerm(
                    perm_ratio=self.configer.get('train_trans', 'perm_ratio')
                )

            if 'random_contrast' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_contrast'] = RandomContrast(
                    lower=self.configer.get('trans_params', 'random_contrast')['lower'],
                    upper=self.configer.get('trans_params', 'random_contrast')['upper'],
                    contrast_ratio=self.configer.get('train_trans', 'contrast_ratio')
                )

            if 'random_pad' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_pad'] = RandomPad(
                    up_scale_range=self.configer.get('trans_params', 'random_pad')['up_scale_range'],
                    pad_ratio=self.configer.get('train_trans', 'pad_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

            if 'random_shift' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_shift'] = RandomShift(
                    shift_pixel=self.configer.get('trans_params', 'random_shift')['shift_pixel'],
                    shift_ratio=self.configer.get('train_trans', 'shift_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

            if 'random_brightness' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_brightness'] = RandomBrightness(
                    shift_value=self.configer.get('trans_params', 'random_brightness')['shift_value'],
                    brightness_ratio=self.configer.get('train_trans', 'brightness_ratio')
                )

            if 'random_hflip' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_hflip'] = RandomHFlip(
                    swap_pair=self.configer.get('trans_params', 'random_hflip')['swap_pair'],
                    flip_ratio=self.configer.get('train_trans', 'flip_ratio')
                )

            if 'random_resize' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                if self.configer.get('trans_params', 'random_resize')['method'] == 'random':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        scale_range=self.configer.get('trans_params', 'random_resize')['scale_range'],
                        resize_ratio=self.configer.get('train_trans', 'resize_ratio')
                    )

                elif self.configer.get('trans_params', 'random_resize')['method'] == 'focus':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        scale_range=self.configer.get('trans_params', 'random_resize')['scale_range'],
                        target_size=self.configer.get('trans_params', 'random_resize')['target_size'],
                        resize_ratio=self.configer.get('train_trans', 'resize_ratio')
                    )

                elif self.configer.get('trans_params', 'random_resize')['method'] == 'bound':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        resize_bound=self.configer.get('trans_params', 'random_resize')['resize_bound'],
                        resize_ratio=self.configer.get('train_trans', 'resize_ratio')
                    )

                else:
                    Log.error('Not Support Resize Method!')
                    exit(1)

            if 'random_crop' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                if self.configer.get('trans_params', 'random_crop')['method'] == 'random':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        crop_ratio=self.configer.get('train_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'center':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        crop_ratio=self.configer.get('train_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'grid':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        grid=self.configer.get('trans_params', 'random_crop')['grid'],
                        crop_ratio=self.configer.get('train_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'focus':
                    self.transforms['random_crop'] = RandomFocusCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        center_jitter=self.configer.get('trans_params', 'random_crop')['center_jitter'],
                        crop_ratio=self.configer.get('train_trans', 'crop_ratio'),
                        mean=self.configer.get('trans_params', 'normalize')['mean_value'],
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'det':
                    self.transforms['random_crop'] = RandomDetCrop(
                        det_crop_ratio=self.configer.get('train_trans', 'crop_ratio')
                    )

                else:
                    Log.error('Not Support Crop Method!')
                    exit(1)

            if 'random_rotate' in self.configer.get('train_trans', 'trans_seq') + shuffle_train_trans:
                self.transforms['random_rotate'] = RandomRotate(
                    max_degree=self.configer.get('trans_params', 'random_rotate')['rotate_degree'],
                    rotate_ratio=self.configer.get('train_trans', 'rotate_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

        else:
            if 'random_saturation' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_saturation'] = RandomSaturation(
                    lower=self.configer.get('trans_params', 'random_saturation')['lower'],
                    upper=self.configer.get('trans_params', 'random_saturation')['upper'],
                    saturation_ratio=self.configer.get('val_trans', 'saturation_ratio')
                )

            if 'random_hue' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_hue'] = RandomHue(
                    delta=self.configer.get('trans_params', 'random_hue')['delta'],
                    hue_ratio=self.configer.get('val_trans', 'hue_ratio')
                )

            if 'random_perm' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_perm'] = RandomPerm(
                    perm_ratio=self.configer.get('val_trans', 'perm_ratio')
                )

            if 'random_contrast' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_contrast'] = RandomContrast(
                    lower=self.configer.get('trans_params', 'random_contrast')['lower'],
                    upper=self.configer.get('trans_params', 'random_contrast')['upper'],
                    contrast_ratio=self.configer.get('val_trans', 'contrast_ratio')
                )

            if 'random_pad' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_pad'] = RandomPad(
                    up_scale_range=self.configer.get('trans_params', 'random_pad')['up_scale_range'],
                    pad_ratio=self.configer.get('val_trans', 'pad_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

            if 'random_shift' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_shift'] = RandomShift(
                    shift_pixel=self.configer.get('trans_params', 'random_shift')['shift_pixel'],
                    shift_ratio=self.configer.get('val_trans', 'shift_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

            if 'random_brightness' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_brightness'] = RandomBrightness(
                    shift_value=self.configer.get('trans_params', 'random_brightness')['shift_value'],
                    brightness_ratio=self.configer.get('val_trans', 'brightness_ratio')
                )

            if 'random_hflip' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_hflip'] = RandomHFlip(
                    swap_pair=self.configer.get('trans_params', 'random_hflip')['swap_pair'],
                    flip_ratio=self.configer.get('val_trans', 'flip_ratio')
                )

            if 'random_resize' in self.configer.get('val_trans', 'trans_seq'):
                if self.configer.get('trans_params', 'random_resize')['method'] == 'random':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        scale_range=self.configer.get('trans_params', 'random_resize')['scale_range'],
                        resize_ratio=self.configer.get('val_trans', 'resize_ratio')
                    )

                elif self.configer.get('trans_params', 'random_resize')['method'] == 'focus':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        scale_range=self.configer.get('trans_params', 'random_resize')['scale_range'],
                        target_size=self.configer.get('trans_params', 'random_resize')['target_size'],
                        resize_ratio=self.configer.get('val_trans', 'resize_ratio')
                    )

                elif self.configer.get('trans_params', 'random_resize')['method'] == 'bound':
                    self.transforms['random_resize'] = RandomResize(
                        method=self.configer.get('trans_params', 'random_resize')['method'],
                        resize_bound=self.configer.get('trans_params', 'random_resize')['resize_bound'],
                        resize_ratio=self.configer.get('val_trans', 'resize_ratio')
                    )

                else:
                    Log.error('Not Support Resize Method!')
                    exit(1)

            if 'random_crop' in self.configer.get('val_trans', 'trans_seq'):
                if self.configer.get('trans_params', 'random_crop')['method'] == 'random':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        crop_ratio=self.configer.get('val_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'center':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        crop_ratio=self.configer.get('val_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'grid':
                    self.transforms['random_crop'] = RandomCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        method=self.configer.get('trans_params', 'random_crop')['method'],
                        grid=self.configer.get('trans_params', 'random_crop')['grid'],
                        crop_ratio=self.configer.get('val_trans', 'crop_ratio'),
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'focus':
                    self.transforms['random_crop'] = RandomFocusCrop(
                        crop_size=self.configer.get('trans_params', 'random_crop')['crop_size'],
                        center_jitter=self.configer.get('trans_params', 'random_crop')['center_jitter'],
                        crop_ratio=self.configer.get('val_trans', 'crop_ratio'),
                        mean=self.configer.get('trans_params', 'normalize')['mean_value'],
                        allow_outside_center=self.configer.get('trans_params', 'random_crop')['allow_outside_center']
                    )

                elif self.configer.get('trans_params', 'random_crop')['method'] == 'det':
                    self.transforms['random_crop'] = RandomDetCrop(
                        det_crop_ratio=self.configer.get('val_trans', 'crop_ratio')
                    )

                else:
                    Log.error('Not Support Crop Method!')
                    exit(1)

            if 'random_rotate' in self.configer.get('val_trans', 'trans_seq'):
                self.transforms['random_rotate'] = RandomRotate(
                    max_degree=self.configer.get('trans_params', 'random_rotate')['rotate_degree'],
                    rotate_ratio=self.configer.get('val_trans', 'rotate_ratio'),
                    mean=self.configer.get('trans_params', 'normalize')['mean_value']
                )

    def __check_none(self, key_list, value_list):
        for key, value in zip(key_list, value_list):
            if value == 'y' and key is None:
                return False

            if value == 'n' and key is not None:
                return False

        return True

    def __call__(self, img, labelmap=None, maskmap=None, kpts=None, bboxes=None, labels=None, polygons=None):

        if self.configer.get('data', 'input_mode') == 'RGB':
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if self.split == 'train':
            shuffle_trans_seq = []
            if not self.configer.is_empty('train_trans', 'shuffle_trans_seq'):
                if isinstance(self.configer.get('train_trans', 'shuffle_trans_seq')[0], list):
                    shuffle_trans_seq_list = self.configer.get('train_trans', 'shuffle_trans_seq')
                    shuffle_trans_seq = shuffle_trans_seq_list[random.randint(0, len(shuffle_trans_seq_list))]
                else:
                    shuffle_trans_seq = self.configer.get('train_trans', 'shuffle_trans_seq')
                    random.shuffle(shuffle_trans_seq)

            for trans_key in (shuffle_trans_seq + self.configer.get('train_trans', 'trans_seq')):
                (img, labelmap, maskmap, kpts,
                 bboxes, labels, polygons) = self.transforms[trans_key](img, labelmap, maskmap,
                                                                           kpts, bboxes, labels, polygons)

        else:
            for trans_key in self.configer.get('val_trans', 'trans_seq'):
                (img, labelmap, maskmap, kpts,
                 bboxes, labels, polygons) = self.transforms[trans_key](img, labelmap, maskmap,
                                                                           kpts, bboxes, labels, polygons)

        if self.configer.get('data', 'input_mode') == 'RGB':
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'n', 'n', 'n', 'n']):
            return img

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['y', 'n', 'n', 'n', 'n', 'n']):
            return img, labelmap

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'n', 'y', 'n', 'n']):
            return img, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'y', 'n', 'n', 'n']):
            return img, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'y', 'y', 'n', 'n']):
            return img, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'y', 'y', 'n', 'n', 'n']):
            return img, maskmap, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['y', 'y', 'y', 'n', 'n', 'n']):
            return img, labelmap, maskmap, kpts

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'y', 'y', 'y', 'n', 'n']):
            return img, maskmap, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['y', 'y', 'y', 'y', 'n', 'n']):
            return img, labelmap, maskmap, kpts, bboxes

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'n', 'y', 'y', 'n']):
            return img, bboxes, labels

        if self.__check_none([labelmap, maskmap, kpts, bboxes, labels, polygons], ['n', 'n', 'n', 'y', 'y', 'y']):
            return img, bboxes, labels, polygons

        Log.error('Params is not valid.')
        exit(1)
