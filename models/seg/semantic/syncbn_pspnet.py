#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Donny You(youansheng@gmail.com)
# Pytorch implementation of PSP net Synchronized Batch Normalization
# this is pytorch implementation of PSP resnet101 (syn-bn) version


import torch
import torch.nn as nn
import torch.nn.functional as F

from extensions.layers.encoding.syncbn import BatchNorm2d
from models.backbones.backbone_selector import BackboneSelector


class _ConvBatchNormReluBlock(nn.Module):
    def __init__(self, inplanes, outplanes, kernel_size, stride, padding=1, dilation=1, relu=True):
        super(_ConvBatchNormReluBlock, self).__init__()
        self.relu = relu
        self.conv =  nn.Conv2d(in_channels=inplanes,out_channels=outplanes,
                            kernel_size=kernel_size, stride=stride, padding=padding,
                            dilation = dilation, bias=False)
        self.bn = BatchNorm2d(num_features=outplanes)
        self.relu_f = nn.ReLU()

    def forward(self, x):
        x = self.bn(self.conv(x))
        if self.relu:
            x = self.relu_f(x)
        return x


# PSP decoder Part
# pyramid pooling, bilinear upsample
class PPMBilinearDeepsup(nn.Module):
    def __init__(self, num_class=150, fc_dim=4096):
        super(PPMBilinearDeepsup, self).__init__()
        pool_scales = (1, 2, 3, 6)
        self.ppm = []
        for scale in pool_scales:
            self.ppm.append(nn.Sequential(
                nn.AdaptiveAvgPool2d(scale),
                nn.Conv2d(fc_dim, 512, kernel_size=1, bias=False),
                BatchNorm2d(512),
                nn.ReLU(inplace=True)
            ))
        self.ppm = nn.ModuleList(self.ppm)
        self.cbr_deepsup = _ConvBatchNormReluBlock(fc_dim // 2, fc_dim // 4, 3, 1)
        self.conv_last = nn.Sequential(
            nn.Conv2d(fc_dim+len(pool_scales)*512, 512,
                      kernel_size=3, padding=1, bias=False),
            BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Dropout2d(0.1),
            nn.Conv2d(512, num_class, kernel_size=1)
        )
        self.conv_last_deepsup = nn.Conv2d(fc_dim // 4, num_class, 1, 1, 0)
        self.dropout_deepsup = nn.Dropout2d(0.1)

    def forward(self, conv_out):
        conv5, conv4 = conv_out
        input_size = conv5.size()
        ppm_out = [conv5]

        for pool_scale in self.ppm:
            ppm_out.append(nn.functional.upsample(
                pool_scale(conv5),
                (input_size[2], input_size[3]),
                mode='bilinear', align_corners=True))

        ppm_out = torch.cat(ppm_out, 1)

        x = self.conv_last(ppm_out)
        aux = self.cbr_deepsup(conv4)
        aux = self.dropout_deepsup(aux)
        aux = self.conv_last_deepsup(aux)

        return x, aux


class SyncBNPSPNet(nn.Sequential):
    def __init__(self, configer):
        super(SyncBNPSPNet, self).__init__()
        self.configer = configer
        self.num_classes = self.configer.get('data', 'num_classes')
        self.backbone = BackboneSelector(configer).get_backbone()

        num_features = self.backbone.get_num_features()

        self.low_features = nn.Sequential(
            self.backbone.conv1, self.backbone.bn1, self.backbone.relu,
            self.backbone.maxpool,
            self.backbone.layer1,
        )
        self.high_features1 = nn.Sequential(self.backbone.layer2, self.backbone.layer3)
        self.high_features2 = nn.Sequential(self.backbone.layer4)
        self.decoder = PPMBilinearDeepsup(num_class=self.num_classes, fc_dim=num_features)

    def forward(self, x):
        low = self.low_features(x)
        aux = self.high_features1(low)
        x = self.high_features2(_)
        x, aux = self.decoder([x, aux])
        x = F.upsample(x, scale_factor=8, mode="bilinear", align_corners=True)

        return [x, aux]


if __name__ == '__main__':
    i = torch.Tensor(1,3,512,512).cuda()
    model = PSPNetResnet(num_classes=19).cuda()
    model.eval()
    o, _ = model(i)
    #print(o.size())
    #final_out = F.upsample(o,scale_factor=8)
    #print(final_out.size())
    print(o.size())
    print(_.size())