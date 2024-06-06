# -*- coding: utf-8 -*- 
# @Time : 2024/3/6 16:40 
# @Author : yangyc
import glob
import json
import re
from typing import *
import requests
from dataclasses import dataclass
from service.base_models.re_model import MixImageTextTable
from service.base_models.xfund_model import XfundDocument, BoundingBox
from requests_toolbelt.multipart.encoder import MultipartEncoder

session = requests.session()


@dataclass
class TableSerService(object):

    @staticmethod
    def predict(table: MixImageTextTable):
        try:
            files, xfundDocument = TableSerService.mix_to_xfund(table)
            mp_encoder = MultipartEncoder(
                fields={
                    'id': list(files.keys())[0],
                    'table_info': xfundDocument.model_dump_json(),
                    'image': [(key, value, 'multipart/form-data') for key, value in files.items()][0],
                }
            )
            headers = {"Content-Type": mp_encoder.content_type}

            res = session.post('http://10.106.24.12:5090/table_ser', data=mp_encoder, headers=headers)
            if res.status_code == 200:
                body = res.json()
                if body['code'] == 0:
                    ner_tags = body['data']
                    return ner_tags
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def mix_to_xfund(table: MixImageTextTable):
        fname = table.table_image.fname
        files = {fname: open(file, 'rb') for file in glob.glob(f'./data/shot*/{fname}.png')}
        assert len(files) > 0
        document = []
        # cellId2Index = {}
        # for index, cell in enumerate(table.cells):
        #     cellId2Index[cell.id] = index

        for cell in table.cells:
            document.append(BoundingBox(id=cell.id,
                                        text=''.join([line.text for line in cell.lines]),
                                        label=cell.label,
                                        box=[int(k) for k in cell.lines[0].bbox]
                                        ))
        return files, XfundDocument(id=table.table_image.fname, document=document, img=table.table_image.model_dump())
