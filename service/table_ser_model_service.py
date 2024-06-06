# -*- coding: utf-8 -*- 
# @Time : 2024/3/6 16:40 
# @Author : yangyc
import copy
import json
import logging
import requests
from dataclasses import dataclass
from service.base_models import MixImageTextTable
from requests_toolbelt.multipart.encoder import MultipartEncoder

logger = logging.getLogger()
session = requests.session()
url = 'http://10.106.24.12:5090/table_ser'


@dataclass
class TableSerModelService(object):

    @staticmethod
    def predict(table: MixImageTextTable):
        """表格语义标签识别"""
        ner_tags = {}
        try:
            fname = table.tableImages[0].md5
            file = (fname, open(f'./data/shot/{fname}.png', 'rb'), 'multipart/form-data')
            mp_encoder = MultipartEncoder(
                fields={
                    'id': fname,
                    'table_info': json.dumps(table.dict(), ensure_ascii=False),
                    'file': file,
                }
            )
            table_print = copy.deepcopy(table)
            table_print.cells = table_print.cells[:8]
            headers = {"Content-Type": mp_encoder.content_type}
            res = session.post(url, data=mp_encoder, headers=headers)
            if res.status_code == 200:
                body = res.json()
                if body['code'] == 0:
                    ner_tags = body['data']
                    return ner_tags
            return ner_tags
        except Exception as e:
            logger.error(e)
            return ner_tags
