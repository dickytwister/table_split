# -*- coding: utf-8 -*-
# @Time : 2024/3/18 17:39
# @Author : yangyc
# 生成xfund数据集
import re
import os
import json
import logging
from collections import defaultdict
from typing import List

from .base_models.xfund_model import XfundDocument, BoundingBox
from .base_models.re_model import MixImageTextTable, Cell, SubLine, Relation
from .base_models.re_model import TagEnum, RelEnum, HEAD_KEYS, TAG_TO_ID, ID_TO_TAG
from .base_models.re_model import MergeTagEnum, MERGE_TAG_TO_ID, MERGE_REL_TAG_TO_ID
import numpy as np

logger = logging.getLogger()


class LabelStudioHelper:
    def __init__(self, filenames):
        dic = {}
        for filename in filenames:
            if not os.path.exists(filename):
                logger.warning(f'LabelStudioHelper:{filename} not exists')
                continue
            with open(filename, 'r', encoding='utf-8') as f:
                cont = f.read()
                for label_studio_data in json.loads(cont):
                    image_id = re.findall(r'[A-Za-z0-9]{8}-(.*?)\.png',
                                          label_studio_data['data']['image'])[0]
                    dic[image_id] = label_studio_data
        self.dic = dic

    def transfer_label_studio_xfund(self, image_id, lines, bboxes, index_boxes):
        n_rows = max(index_box[2] for index_box in index_boxes)
        n_cols = max(index_box[3] for index_box in index_boxes)
        table_arr = np.zeros((n_rows, n_cols))
        tag_arr = np.zeros((n_rows, n_cols))
        label_studio_data = self.dic[image_id]
        label_studio_relation_dict = defaultdict(list)
        label_studio_box_dict = dict()
        annotations = label_studio_data['annotations'][0]['result']
        if not annotations:
            return None
        width0, height0 = None, None
        # 文本框坐标还原
        for annotation in annotations:
            if annotation['type'] == 'rectanglelabels':
                width0 = annotation['original_width']
                height0 = annotation['original_height']
                label_studio_box = annotation['value']
                x = label_studio_box['x'] * width0 / 100
                width = label_studio_box['width'] * width0 / 100
                y = label_studio_box['y'] * height0 / 100
                height = label_studio_box['height'] * height0 / 100
                bbox = [int(x), int(y), int(x + width), int(y + height)]
                label_studio_box_dict[annotation['id']] = {'box': bbox,
                                                           'id': annotation['id'],
                                                           'label': label_studio_box['rectanglelabels'][0]}
            elif annotation['type'] == 'relation':
                label_studio_relation_dict[annotation['from_id']].append(annotation['to_id'])

        img = {"fname": image_id + '.png',
               "width": width0,
               "height": height0}
        document = []
        cells = []
        ls_id_cell_id_mapping = {}
        cell_id_ls_id_mapping = {}
        filterList = ['', '-', '--', '无', '指']
        count = 0
        for cell_id in range(len(index_boxes)):
            index_box = index_boxes[cell_id]
            a, b, c, d = index_box
            label_studio_box = self.find_best_match(image_id, bboxes[cell_id], label_studio_box_dict)
            if label_studio_box is None:
                label = 'other'
            elif lines[cell_id] in filterList:
                label = 'other'
            else:
                label = {"key": "key",
                         "value": "value",
                         "total": "total",
                         "title": "title",
                         "project": "project",
                         "remark": "other",
                         }.get(label_studio_box['label'], 'other')
            cells.append(Cell(id=cell_id,
                              subLines=[SubLine(pageNumber=0, box=bboxes[cell_id], text=lines[cell_id])],
                              indexBox=index_box,
                              labelId=TAG_TO_ID[label.upper()]
                              ))
            table_arr[a:c, b:d] = cell_id
            tag_arr[a:c, b:d] = TAG_TO_ID[label.upper()]
            if label_studio_box:
                ls_id_cell_id_mapping[label_studio_box['id']] = cell_id
                cell_id_ls_id_mapping[cell_id] = label_studio_box['id']
        # print(image_id)
        infered_rels = self.get_relations(table_arr, tag_arr, cells)
        records = self.to_records(image_id, cells, infered_rels, filterList)

        relation_dict = defaultdict(list)
        for ls_from_id, ls_to_id_list in label_studio_relation_dict.items():
            for ls_to_id in ls_to_id_list:
                relation_dict[ls_id_cell_id_mapping[ls_from_id]].append(ls_id_cell_id_mapping[ls_to_id])

        for cell_id in range(len(index_boxes)):
            cell = cells[cell_id]
            index_box = index_boxes[cell_id]
            linking = []
            if cell_id in cell_id_ls_id_mapping:
                if cell_id in relation_dict:
                    from_id = cell_id
                    to_id_list = relation_dict[from_id]
                    for to_id in to_id_list:
                        linking.append([from_id, to_id])

            document.append(BoundingBox(id=cell_id,
                                        text=cell.subLines[0].text,
                                        label=ID_TO_TAG[cell.labelId],
                                        box=cell.subLines[0].box,
                                        indexBox=index_box,
                                        linking=linking))

        xfundDocument = XfundDocument(id=image_id, document=document, img=img) if document else None
        return xfundDocument

    def transfer_ls_to_xfund_textmerge(self, ocr_data_with_bbox: List[MixImageTextTable]):
        new_data = []
        for d in ocr_data_with_bbox:
            image_id = d.id
            if image_id not in self.dic:
                continue
            label_studio_data = self.dic[image_id]
            label_studio_relation_dict = defaultdict(list)
            label_studio_type_dict = dict()
            annotations = label_studio_data['annotations'][0]['result']
            if not annotations:
                continue
            for annotation in annotations:
                if annotation['type'] == 'rectanglelabels':
                    label_studio_box = annotation['value']
                    label_studio_type_dict[annotation['id']] = label_studio_box['rectanglelabels'][0]
                elif annotation['type'] == 'relation':
                    label_studio_relation_dict[annotation['from_id']].append((annotation['to_id'], annotation['labels']))
            relations = []
            id_list = []
            for from_id, li in label_studio_relation_dict.items():
                for to_id, rel_labels in li:
                    if rel_labels:
                        from_id, to_id = int(from_id), int(to_id)
                        id_list.append((from_id, to_id))
                        relations.append(Relation(fromId=from_id, toId=to_id,
                                                  labelId=MERGE_REL_TAG_TO_ID.get(rel_labels[0].upper(), 0)))
            d.relations = relations
            cells = {int(cell.id): cell for cell in d.cells}
            id_list.sort()
            new_cells = []
            for from_id, to_id in id_list:
                cell = cells[from_id]
                label_type = label_studio_type_dict.get(str(cell.id), 'other')
                cell.labelId = MERGE_TAG_TO_ID.get(label_type.upper(), 0)
                cell = cells[to_id]
                label_type = label_studio_type_dict.get(str(cell.id), 'other')
                cell.labelId = MERGE_TAG_TO_ID.get(label_type.upper(), 0)

                new_cells += [cells[from_id], cells[to_id]]
            d.cells = new_cells
            new_data.append(d)

        return new_data

    def find_best_match(self, image_id, box1, label_studio_box_dict):
        if box1 is None:
            return
        iou_list = []
        box_id_list = []
        for box_id, data in label_studio_box_dict.items():
            box2 = data['box']
            iou_list.append(self.calculate_iou(box1, box2)[0])
            box_id_list.append(box_id)
        best_i = list(sorted(range(len(iou_list)), key=lambda x: iou_list[x], reverse=True))[0]
        best_box_id = box_id_list[best_i]
        max_iou = iou_list[best_i]
        if max_iou > 0.5:
            return label_studio_box_dict[best_box_id]
        elif max_iou > 0.25:
            print(image_id, max_iou)
            return

    @staticmethod
    def calculate_iou(box1, box2, in_thresh=0.9):
        iou_trunc_by_1_in_2 = 0.0
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        # 计算交集区域的坐标
        x_left = max(x1_1, x1_2)
        y_top = max(y1_1, y1_2)
        x_right = min(x2_1, x2_2)
        y_bottom = min(y2_1, y2_2)
        # 如果没有交集，IoU为0
        if x_right < x_left or y_bottom < y_top:
            return 0.0, iou_trunc_by_1_in_2
        # 计算交集和并集的面积
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = float(box1_area + box2_area - intersection_area)
        # 计算IoU
        iou = intersection_area / union_area
        if iou > 0.0 and box1_area / iou > in_thresh:
            iou_trunc_by_1_in_2 = iou

        return iou, iou_trunc_by_1_in_2

    def get_relations(self, table_arr: np.ndarray, tag_arr: np.ndarray, cells: List[Cell]):
        relations = []
        has_title_list = (tag_arr == TagEnum.title.value).all(axis=1)
        has_project_list = tag_arr[:, 0] == TagEnum.project.value

        sep_list = [sep_id for sep_id, flag in enumerate((has_title_list | has_project_list)) if flag] + [-1]
        title_id_list = []
        if len(sep_list) == 1:
            relations += self.get_subtable_relations(table_arr, tag_arr, cells, [], None)
        else:
            global_header_tags = tag_arr[0: sep_list[0]]
            global_params = []
            if global_header_tags.size > 0 and any(k for k in global_header_tags[0].tolist()):
                global_header_table = table_arr[0: sep_list[0]]
                global_cells = cells[0: int(global_header_table.max()) + 1]
                header_rels = self.get_subtable_relations(global_header_table, global_header_tags,
                                                          global_cells,
                                                          [], [])
                global_params = [global_header_tags, global_header_table, global_cells]
                relations += header_rels

            for start, end in zip(sep_list[:-1], sep_list[1:]):
                if end == -1:
                    end = tag_arr.shape[1]
                sub_table = table_arr[start:end]
                sub_tag = tag_arr[start:end]
                if sub_table.size > 0:
                    prior_ids = []
                    for i in range(2):
                        for j in range(2):
                            if (i < sub_tag.shape[0] and j < sub_tag.shape[1] and
                                    sub_tag[i, j] in [TagEnum.project.value, TagEnum.title.value]):
                                prior_ids.append(int(sub_table[i, j]))
                    prior_ids = list(sorted(set(prior_ids)))
                    max_id = int(sub_table.max())
                    relations += self.get_subtable_relations(table_arr, tag_arr, cells[prior_ids[-1] + 1:max_id + 1],
                                                             prior_ids, global_params)
                    title_id_list.append(prior_ids[0])

        return relations

    def get_subtable_relations(self, table_arr, tag_arr, cells: List[Cell], prior_ids, global_params) -> List[Relation]:
        # 单元格区间
        relations = []
        try:
            hasAnyKey = False
            for cell in cells:
                if cell.labelId in HEAD_KEYS:
                    flag = True
                    break
            if hasAnyKey:
                cells_map = {cell.id: cell for cell in cells}
                for cell in cells:
                    x1, y1, x2, y2 = cell.indexBox
                    if tag_arr[x1, y1] == TagEnum.key.value:
                        # flag=True:横向key比纵向key数量多，不做横向关系搜索;False做横向关系搜索
                        flag1 = sum(k in HEAD_KEYS for k in tag_arr[x1, y1 - 2:y1 + 2]
                                    ) < sum(k in HEAD_KEYS for k in tag_arr[x1 - 2:x1 + 2, y1])
                        # 横向关系搜索
                        if not flag1 and y1 >= 1 and tag_arr[x1, y1 - 1] in HEAD_KEYS:
                            cell_index = table_arr[x1, y1 - 1].astype(int)
                            if cell_index not in cells_map:
                                continue
                            from_id = cells_map[cell_index].id
                            indexBox = cells_map[cell_index].indexBox
                            if self.range_contain(cell.indexBox, indexBox, axis=0, strict=True):
                                relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.belongTo.value))
                                continue
                        # 纵向关系搜索
                        if x1 >= 1 and tag_arr[x1 - 1, y1] in HEAD_KEYS:
                            cell_index = table_arr[x1 - 1, y1].astype(int)
                            if cell_index not in cells_map:
                                continue
                            from_id = cells_map[cell_index].id
                            indexBox = cells_map[cell_index].indexBox
                            if self.range_contain(cell.indexBox, indexBox, axis=1, strict=True):
                                relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.belongTo.value))
                                continue
                    if tag_arr[x1, y1] == TagEnum.value.value:
                        # 横向关系搜索
                        y = y1 - 1
                        while y >= 0:
                            if tag_arr[x1, y] in HEAD_KEYS:
                                cell_index = table_arr[x1, y].astype(int)
                                if cell_index not in cells_map:
                                    break
                                from_id = cells_map[cell_index].id
                                indexBox = cells_map[cell_index].indexBox
                                if self.range_contain(cell.indexBox, indexBox, axis=0):
                                    relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.valueIs.value))
                                    break
                            y -= 1
                        # 纵向关系搜索
                        x = x1 - 1
                        while x >= 0:
                            if tag_arr[x, y1] in HEAD_KEYS:
                                cell_index = table_arr[x, y1].astype(int)
                                if cell_index not in cells_map:
                                    break
                                from_id = cells_map[cell_index].id
                                indexBox = cells_map[cell_index].indexBox
                                if self.range_contain(cell.indexBox, indexBox, axis=1):
                                    relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.valueIs.value))
                                    break
                            x -= 1
            else:
                if global_params:
                    global_header_tags, global_header_tables, global_cells = global_params
                    for cell in cells:
                        x1, y1, x2, y2 = cell.indexBox
                        x = global_header_tags.shape[0] - 1
                        while x >= 0:
                            if global_header_tags[x, y1] in HEAD_KEYS:
                                cell_index = global_header_tables[x, y1].astype(int)
                                from_id = global_cells[cell_index].id
                                indexBox = global_cells[cell_index].indexBox
                                if self.range_contain(cell.indexBox, indexBox, axis=1):
                                    relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.valueIs.value))
                                    break
                            x -= 1
            if cells:
                line_start = cells[0].indexBox[0]
                line_end = table_arr.shape[1]

                col_start = cells[0].indexBox[1]
                col_end = cells[-1].indexBox[3]

                if len(prior_ids) >= 2:
                    for p1, p2 in zip(prior_ids[:-1], prior_ids[1:]):
                        relations.append(Relation(fromId=p1, toId=p2, labelId=RelEnum.belongTo.value))
                elif prior_ids:
                    col_tags = {s: t for s, t in zip(table_arr[line_start, col_start: col_end],
                                                     tag_arr[line_start, col_start: col_end])}
                    row_tags = {s: t for s, t in zip(table_arr[line_start: line_end, 0],
                                                     tag_arr[line_start: line_end, 0])}
                    if not hasAnyKey:
                        for cell in cells:
                            from_id = prior_ids[-1]
                            to_id = cell.id
                            if cell.labelId == TagEnum.value.value:
                                relations.append(Relation(fromId=from_id, toId=to_id, labelId=RelEnum.valueIs.value))
                    elif all(k != TagEnum.other.value for k in col_tags.values()):
                        for cell_id, label_id in col_tags.items():
                            if label_id in HEAD_KEYS:
                                from_id = prior_ids[-1]
                                relations.append(Relation(fromId=from_id, toId=cell_id, labelId=RelEnum.belongTo.value))
                    elif all(k != TagEnum.other.value for k in row_tags.values()):
                        for cell_id, label_id in row_tags.items():
                            if label_id in HEAD_KEYS:
                                from_id = prior_ids[-1]
                                relations.append(Relation(fromId=from_id, toId=cell_id, labelId=RelEnum.belongTo.value))
        except Exception as e:
            print(e)
            import traceback
            print(traceback.format_exc())
            relations = []
        return relations

    @staticmethod
    def range_contain(table_box1, table_box2, axis=0, strict=False):
        if strict:
            if axis == 1:
                return (table_box2[1] <= table_box1[1] and table_box1[3] <= table_box2[3] and
                        table_box1[3] - table_box1[1] < table_box2[3] - table_box2[1])
            else:
                return (table_box2[0] <= table_box1[0] and table_box1[2] <= table_box2[2] and
                        table_box1[2] - table_box1[0] < table_box2[2] - table_box2[0])
        else:
            if axis == 1:
                return table_box2[1] <= table_box1[1] and table_box1[3] <= table_box2[3]
            else:
                return table_box2[0] <= table_box1[0] and table_box1[2] <= table_box2[2]

    @staticmethod
    def to_records(image_id, cells: List[Cell], relations: List[Relation], filterList):
        if not cells and not relations:
            return {}
        relations.sort(key=lambda x: (int(x.fromId), int(x.toId)))
        key2key = {}
        value2key = defaultdict(list)
        records = defaultdict(list)
        id2text = {}
        for cell in cells:
            text = ''.join([line.text for line in cell.subLines])
            id2text[int(cell.id)] = text
        for relation in relations:
            from_id = int(relation.fromId)
            to_id = int(relation.toId)
            if from_id > to_id:
                from_id, to_id = to_id, from_id
            elif from_id == to_id:
                continue
            if to_id >= len(cells):
                print(image_id, 'to_records error')
                return {}
            a = cells[from_id].labelId
            b = cells[to_id].labelId
            if relation.labelId == RelEnum.belongTo.value:
                if a in HEAD_KEYS and b in HEAD_KEYS:
                    key2key[to_id] = from_id
            if relation.labelId == RelEnum.valueIs.value:
                if a in HEAD_KEYS and b == TagEnum.value.value:
                    value2key[to_id].append(from_id)
        raw_records = []
        for value_id, key_id_list in sorted(value2key.items(), key=lambda x: (x[0], x[1][0])):
            value = id2text[value_id]
            if value in filterList:
                continue
            pre_ids_list = []
            for pre_id in key_id_list:
                pre_ids = [pre_id]
                while pre_id in key2key:
                    pre_id = key2key[pre_id]
                    pre_ids.append(pre_id)
                if pre_ids:
                    pre_ids_list.append(pre_ids)

            for pre_ids in pre_ids_list:
                pre_ids.sort()
            pre_ids_list.sort(key=lambda x: x[0])
            raw_records.append((pre_ids_list, value_id))

        raw_records.sort(key=lambda x: (*(k[0] for k in x[0]), x[1]))
        for pre_ids_list, value_id in raw_records:
            pre_ids = []
            for p in pre_ids_list:
                pre_ids += p
            records['|'.join(id2text[pre_id] for pre_id in pre_ids)].append(id2text[value_id])

        return records
