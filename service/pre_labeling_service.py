# -*- coding: utf-8 -*- 
# @Time : 2024/3/20 9:39 
# @Author : yangyc
import json
import random
from typing import List, Optional, Union

import numpy as np
from pydantic import BaseModel

from service.table_re_service import SimpleTable, ComplexTable, TagEnum, RelEnum
from service.base_models.ls_model import AnnoBox, BoxValue, AnnoRelation


def merge_bbox(bbox_list):
    x0, y0, x1, y1 = list(zip(*bbox_list))
    return [min(x0), min(y0), max(x1), max(y1)]


class PreLabelingHelper:
    def __init__(self, ocr_data):
        self.ocr_data = ocr_data

    def pre_labeling(self, filename1, filename2):
        result1 = {}
        result2 = {}
        for d in self.ocr_data:
            image_id = d['image_id']
            original_height = d['original_height']
            original_width = d['original_width']
            lines = d['lines']
            bboxes = d['bboxes']
            st: Optional[Union[ComplexTable]] = d['st']
            if d['is_simple']:
                ner_tags, relations = self.ct2box_relation(st, original_height, original_width)
                result1[image_id] = ner_tags + relations
            else:
                ner_tags, relations = self.ct2box_relation(st, original_height, original_width)
                result2[image_id] = ner_tags + relations

        with open(filename1, 'w', encoding='utf-8') as f:
            f.write(json.dumps(result1, ensure_ascii=False))
        with open(filename2, 'w', encoding='utf-8') as f:
            f.write(json.dumps(result2, ensure_ascii=False))
        return len(result1), len(result2)

    def ct2box_relation(self, st: ComplexTable, original_height, original_width):
        ner_tags = []
        for cell in st.cells:
            cell_text = ''.join([k.text for k in cell.lines])
            if cell_text.strip() in ['-', '', '--', '指'] or cell.lines[0].bbox is None:
                continue
            x, y, width, height = self.transform_size(cell.lines[0].bbox, original_height, original_width)
            ner_tag = AnnoBox(id=self.random_str(),
                              original_width=original_width,
                              original_height=original_height,
                              value=BoxValue(x=x, y=y, width=width, height=height,
                                             rectanglelabels=[cell.label])
                              )
            ner_tags.append(ner_tag.dict())
        return ner_tags, []

    def st2box_relation(self, st: SimpleTable, lines, bboxes, original_height, original_width):
        if not st or not st.has_data:
            ner_tags = []
            for line, bbox in zip(lines, bboxes):
                if line.strip() in ['-', '', '--'] or bbox is None:
                    continue
                x, y, width, height = self.transform_size(bbox, original_height, original_width)
                ner_tag = AnnoBox(id=self.random_str(),
                                  original_width=original_width,
                                  original_height=original_height,
                                  value=BoxValue(x=x, y=y, width=width, height=height)
                                  )
                ner_tags.append(ner_tag.dict())
            return ner_tags, []
        tags = {
            TagEnum.key.value: TagEnum.key.name,
            TagEnum.value.value: TagEnum.value.name,
            TagEnum.title.value: TagEnum.title.name,
            TagEnum.total.value: TagEnum.total.name,
            TagEnum.project.value: TagEnum.total.name,
        }
        rels = {
            RelEnum.agg_to.value: ['合并'],
            RelEnum.belong_to.value: ['从属'],
            RelEnum.value_is.value: ['取值'],
        }

        ner_arr = st.ner_arr
        rel_arr = st.rel_arr
        cond1 = rel_arr == RelEnum.value_is.value
        cond2 = rel_arr == RelEnum.belong_to.value
        cond3 = rel_arr == RelEnum.agg_to.value
        arg_result = np.argwhere(cond1 | cond2 | cond3).tolist()
        labels = []
        ner_tags = []
        relations = []
        for row in ner_arr:
            for col in row:
                labels.append(tags.get(int(col), 'other'))
        filtered = []
        for line, bbox, label in zip(lines, bboxes, labels):
            if bbox is None:
                ner_tags.append(None)
                filtered.append(len(ner_tags) - 1)
                continue
            x, y, width, height = self.transform_size(bbox, original_height, original_width)
            ner_tag = AnnoBox(id=self.random_str(),
                              original_width=original_width,
                              original_height=original_height,
                              value=BoxValue(x=x, y=y, width=width, height=height, rectanglelabels=[label])
                              )
            ner_tags.append(ner_tag)
            if line.strip() in st.filterList:
                filtered.append(len(ner_tags) - 1)
        for x, y in arg_result:
            if x in filtered or y in filtered:
                continue
            from_id = ner_tags[x].id
            to_id = ner_tags[y].id
            labels = rels.get(int(rel_arr[x][y]), [])
            relations.append(AnnoRelation(from_id=from_id, to_id=to_id, labels=labels))
        filtered.reverse()
        for index in filtered:
            ner_tags.pop(index)
        ner_tags = [k.dict() for k in ner_tags]
        relations = [k.dict() for k in relations]
        return ner_tags, relations

    @staticmethod
    def transform_size(bbox, original_height, original_width):

        x1, y1, x2, y2 = bbox
        x = x1 * 100.0 / original_width
        y = y1 * 100.0 / original_height
        width = (x2 - x1) * 100.0 / original_width
        height = (y2 - y1) * 100.0 / original_height
        return x, y, width, height

    @staticmethod
    def random_str():
        cands = list(range(ord('A'), ord('Z') + 1)) + list(range(ord('a'), ord('z') + 1)) + list(range(ord('0'), ord('9')))
        cands = [chr(k) for k in cands]
        buffer = []
        for i in range(10):
            buffer.append(random.choice(cands))
        return ''.join(buffer)
