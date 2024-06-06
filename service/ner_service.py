# -*- coding: utf-8 -*- 
# @Time : 2024/3/27 18:39 
# @Author : yangyc
# -*- coding: utf-8 -*-
# @Time : 2024/3/6 16:40
# @Author : yangyc
import re
from typing import *
import requests
from dataclasses import dataclass
from config import setting

session = requests.session()
gilner_url = setting.gilner_url


@dataclass
class NerResponse:
    code: int
    labels: List[int]
    message: str = None


@dataclass
class NerService(object):

    @staticmethod
    def call(sents: List[str]):
        try:
            sent_dict = {i: sent.replace("\n", "") for i, sent in enumerate(sents)
                         if sent not in ['', '-', '--', '是', '否', '中国', '无', '本人']
                         and not re.fullmatch(r'[+-]?\d[\d,.、]*%?|[a-zA-Z .]+|\d{4}年\d{1,2}月\d{1,2}日', sent, flags=re.S)
                         and len(sent) < 50
                         }
            res = session.post(gilner_url, json={'text': '\n'.join(sent_dict.values())})

            if res.status_code == 200:
                body = res.json()
                if body['code'] == 0:
                    code = body['code']
                    labels = [1] * len(sents)
                    mentions = set()
                    for m in body['mentions']:
                        mentions.add(m['mention'])
                    for i in range(len(sents)):
                        if i not in sent_dict:
                            labels[i] = 0
                        else:
                            if any(mention in sent_dict[i] for mention in mentions):
                                labels[i] = 0

                    return NerResponse(code, labels)
            return NerResponse(-1, [])
        except Exception as e:
            return NerResponse(-1, [], str(e))


if __name__ == '__main__':
    print(NerService.call(['股票简称', '林兆雄', '股票代码', '000028']))
