# -*- coding: utf-8 -*- 
# @Time : 2024/3/6 16:40 
# @Author : yangyc
import re
from typing import *
import requests
from dataclasses import dataclass
from config.config import setting

session = requests.session()
table_head_url = setting.table_head_url


@dataclass
class TableHeadModel:
    code: int
    labels: List[int]
    message: str = None


@dataclass
class TableHeadService(object):

    @staticmethod
    def call(sents: List[str]):
        try:
            sent_dict = {i: sent for i, sent in enumerate(sents)
                         if sent not in ['', '-', '--'] and
                         not re.fullmatch(r'\d[\d,.]*%?', sent, flags=re.S)
                         }
            res = session.post(table_head_url, json={'sens': list(sent_dict.values())})
            if res.status_code == 200:
                body = res.json()
                if body['code'] == 0:
                    code = body['code']
                    labels = [0] * len(sents)
                    for i, label in zip(sent_dict.keys(), body['data']):
                        labels[i] = label

                    return TableHeadModel(code, labels)
            return TableHeadModel(-1, [])
        except Exception as e:
            return TableHeadModel(-1, [], str(e))


if __name__ == '__main__':
    print(TableHeadService.call(['股票简称', '英洛华', '股票代码', '000795']))
