#!/usr/bin/env bash
# -*- coding:utf-8 -*-
# Author: Donny You(youansheng@gmail.com)
# Generate train & val data.


export PYTHONPATH='/home/donny/Projects/PytorchCV'


ROOT_DIR='/home/donny/DataSet/VOC/VOCdevkit/VOC2007'
SAVE_DIR='/home/donny/DataSet/VOC2007_DET'


python2.7 voc_det_generator.py --root_dir $ROOT_DIR \
                               --save_dir $SAVE_DIR
