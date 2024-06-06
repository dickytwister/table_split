# -*- coding: utf-8 -*- 
# @Time : 2024/3/13 17:05 
# @Author : yangyc
import re
import logging
from collections import defaultdict
from typing import List, Tuple, Dict, Union, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass
from bs4.element import Tag
from service.labling_service import LabelStudioHelper
from service import TableSerModelService
from service.base_models.re_model import (Cell, Relation, RelEnum, TagEnum, HEAD_KEYS,
                                          TableImage, MixImageTextTable, SubLine, SubCell)

logger = logging.getLogger()


@dataclass
class BaseTable:
    image_id: str
    num_rows: int = -1
    num_cols: int = -1
    filterList = ['-', '', '--', '指']
    table_arr: Optional[np.ndarray] = None
    cells: Optional[List[Cell]] = None
    relations: Optional[List[Relation]] = None

    def to_records(self):
        if not self.cells and not self.relations:
            return []
        self.relations.sort(key=lambda x: (int(x.fromId), int(x.toId)))
        key2key = {}
        value2key = defaultdict(list)
        records = []
        id2text = {}
        for cell in self.cells:
            text = ''.join([line.text for line in cell.subLines])
            id2text[int(cell.id)] = text
        for relation in self.relations:
            from_id = int(relation.fromId)
            to_id = int(relation.toId)
            if from_id > to_id:
                from_id, to_id = to_id, from_id
            elif from_id == to_id:
                continue
            a = self.cells[from_id].labelId
            b = self.cells[to_id].labelId
            if relation.labelId == RelEnum.belongTo.value:
                if a in HEAD_KEYS and b in HEAD_KEYS:
                    key2key[from_id] = to_id
            if relation.labelId == RelEnum.valueIs.value:
                if a in HEAD_KEYS and b == TagEnum.value.value:
                    value2key[to_id].append(from_id)
        raw_records = []
        for value_id, key_id_list in sorted(value2key.items(), key=lambda x: (x[0], x[1][0])):
            value = id2text[value_id]
            if value in self.filterList:
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
            records.append({
                '|'.join(id2text[pre_id] for pre_id in pre_ids): id2text[value_id]
            })
        return records

    @staticmethod
    def is_simple(table_rows: List[List[Tag]]):
        flag = True
        for row in table_rows:
            for cell in row:
                if cell.attrs.get('colspan') or cell.attrs.get('rowspan'):
                    flag = False
                    break
        return flag


class ComplexTable(BaseTable):

    def __init__(self, image_id,
                 table_rows: List[List[Tag]],
                 bboxes: List[List[int]],
                 cell_boxes: Optional[List[List[int]]],
                 helper: LabelStudioHelper, height, width):
        super().__init__(image_id=image_id)
        self.use_table_ser = True
        self.cells, self.table_arr = self.build_cells_and_grids(table_rows, bboxes, cell_boxes)
        self.table_images = [TableImage(md5=image_id, width=width, height=height)]
        self.assign_cell_labels(self.image_id, helper)
        self.relations = self.get_relations()

    def build_cells_and_grids(self, table_rows, bboxes: List[List[int]], cell_boxes: List[List[int]]):
        cols_list = []
        for row in table_rows:
            s = 0
            for cell in row:
                s += int(cell.get('colspan') or 1)
            cols_list.append(s)
        num_cols = max(cols_list)
        table_arr = np.zeros((1, num_cols))
        cell_id = 0
        index = 0
        cells = []
        for i in range(len(table_rows)):
            col_start = 0
            for j in range(len(table_rows[i])):
                cell = table_rows[i][j]
                row_span = int(cell.get('rowspan') or 1)
                col_span = int(cell.get('colspan') or 1)
                if i != len(table_rows) - 1 and i + row_span + 1 > len(table_arr):
                    for k in range(len(table_arr), i + row_span + 1):
                        table_arr = np.concatenate([table_arr, np.zeros((1, num_cols))], axis=0)

                while col_start < num_cols and table_arr[i][col_start] != 0:
                    col_start += 1
                if col_start == num_cols and table_arr[i][col_start] == 1:
                    raise Exception(f'{self.image_id} table rows parse error')
                table_arr[i: i + row_span, col_start: col_start + col_span] = cell_id

                subLines = [SubLine(pageNumber=0, text=cell.text, box=bboxes[index])]
                subCells = [SubCell(pageNumber=0, box=cell_boxes[index])] if cell_boxes else None
                cell_object = Cell(id=cell_id,
                                   label=TagEnum.other.value,
                                   subLines=subLines,
                                   subCells=subCells,
                                   indexBox=(i, col_start, i + row_span, col_start + col_span),
                                   )
                cells.append(cell_object)
                col_start = col_start + col_span
                index += 1
                cell_id += 1

        return cells, table_arr

    def assign_cell_labels(self, image_id, helper: LabelStudioHelper):
        subLines = []
        bboxes = []
        indexBoxes = []
        for cell in self.cells:
            subLines.append(''.join(k.text for k in cell.subLines))
            bboxes.append(cell.subLines[0].box)
            indexBoxes.append(cell.indexBox)
        if not self.use_table_ser:
            # xfundDocument = helper.transfer_label_studio_xfund(image_id, subLines, bboxes, indexBoxes)
            # for cell, d in zip(self.cells, xfundDocument.document):
            #     cell.labelId = d.label
            pass
        else:
            id = self.table_images[0].md5
            mixImageTextTable = MixImageTextTable(id=id,
                                                  nRows=self.table_arr.shape[0],
                                                  nCols=self.table_arr.shape[1],
                                                  tableImages=self.table_images,
                                                  cells=self.cells)
            ner_tags = TableSerModelService.predict(mixImageTextTable)
            for cell in self.cells:
                cell.labelId = ner_tags.get(cell.id, TagEnum.other.value)

    def get_relations(self):
        # 遍历单元格
        tag_arr = np.zeros_like(self.table_arr)
        # 获取单元格分类标签
        for cell in self.cells:
            cell_id = int(cell.id)
            tag_arr = np.where(self.table_arr == cell_id, cell.labelId, tag_arr)
        # 单元格区间
        relations = []
        for cell in self.cells:
            x1, y1, x2, y2 = cell.indexBox
            if cell.labelId == TagEnum.key.value:
                # flag=True:横向key比纵向key数量多;不做横向关系搜索
                flag = sum(k in HEAD_KEYS for k in tag_arr[x1, y1 - 2:y1 + 2]
                           ) < sum(k in HEAD_KEYS for k in tag_arr[x1 - 2:x1 + 2, y1])
                # 横向关系搜索
                if not flag and y1 >= 1 and tag_arr[x1, y1 - 1] in HEAD_KEYS:
                    cell_index = self.table_arr[x1, y1 - 1].astype(int)
                    from_id = self.cells[cell_index].id
                    indexBox = self.cells[cell_index].indexBox
                    if self.range_contain(cell.indexBox, indexBox, axis=0, strict=True):
                        relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.belongTo.value))
                        continue
                # 纵向关系搜索
                if x1 >= 1 and tag_arr[x1 - 1, y1] in HEAD_KEYS:
                    table_i = self.table_arr[x1 - 1, y1].astype(int)
                    from_id = self.cells[table_i].id
                    indexBox = self.cells[table_i].indexBox
                    if self.range_contain(cell.indexBox, indexBox, axis=1, strict=True):
                        relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.belongTo.value))
                        continue
            if cell.labelId == TagEnum.value.value:
                # 横向关系搜索
                y = y1 - 1
                while y >= 0:
                    if tag_arr[x1, y] in HEAD_KEYS:
                        cell_index = self.table_arr[x1, y].astype(int)
                        from_id = self.cells[cell_index].id
                        indexBox = self.cells[cell_index].indexBox
                        if self.range_contain(cell.indexBox, indexBox, axis=0):
                            relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.valueIs.value))
                            break
                    y -= 1
                # 纵向关系搜索
                x = x1 - 1
                while x >= 0:
                    if tag_arr[x, y1] in HEAD_KEYS:
                        cell_index = self.table_arr[x, y1].astype(int)
                        from_id = self.cells[cell_index].id
                        indexBox = self.cells[cell_index].indexBox
                        if self.range_contain(cell.indexBox, indexBox, axis=1):
                            relations.append(Relation(fromId=from_id, toId=cell.id, labelId=RelEnum.valueIs.value))
                            break
                    x -= 1
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


class SimpleTable(BaseTable):

    def __init__(self, image_id, table_rows: List[List[Tag]]):
        super().__init__(image_id=image_id)
        self.table_rows = table_rows
        self.num_rows = len(self.table_rows)
        self.num_cols = max(len(row) for row in self.table_rows)

        self.rel_arr = np.zeros((self.num_rows * self.num_cols, self.num_rows * self.num_cols))
        self.ner_arr = np.ones((self.num_rows, self.num_cols)) * TagEnum.value.value

        self.k_v_pairs: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        self.ks_v_pairs: Dict[Tuple[Tuple[int, int], ...], List[Tuple[int, int]]] = defaultdict(list)
        self.kv_output: List[Dict] = []
        self.has_data = False

    def get_sparse_ner_tags(self):
        tags = np.argwhere(self.ner_arr.reshape(-1) == 1).tolist()
        return [tag[0] for tag in tags]

    def get_sparse_relations(self):
        rels = np.argwhere(self.ner_arr.reshape(-1) == 1).tolist()
        return {(rel[0], rel[1]): 1 for rel in rels}

    def get_head_list(self, index=0, axis=0, start=0):
        """
        axis=0第一行
        axis=1第一列
        """
        if axis == 0:
            return [col.text for col in self.table_rows[index]][start:]
        elif axis == 1:
            return [row[index].text for row in self.table_rows][start:]

    def set_b2b_relations(self, left, right, rel_value, index_range: Tuple[int, int], axis=0):
        """
        axis=0
        横向:left行与right行对应元素设置关系rel_value
        axis=1
        纵向:left列与right列对应元素设置关系rel_value
        """
        start, end = index_range
        if axis == 0:
            for k in list(range(self.num_cols))[start:end]:
                self.rel_arr[left * self.num_cols + k, right * self.num_cols + k] = rel_value
        elif axis == 1:
            for k in list(range(self.num_rows))[start:end]:
                self.rel_arr[k * self.num_cols + left, k * self.num_cols + right] = rel_value

    def set_b_relations(self, i, j, a, b, c, d, rel_value):
        """设置table[i,j]到table[a:b,c:d]的关系"""
        left_index = i * self.num_cols + j
        for i1 in range(a, b):
            for j1 in range(c, d):
                right_index = i1 * self.num_cols + j1
                self.rel_arr[left_index, right_index] = rel_value

    def set_total_tag_relations(self, axis=0):
        """设置合并项"""
        if axis == 0:
            for i, row in enumerate(self.table_rows):
                if row[0].text and re.sub(r"\s+", "", row[0].text, flags=re.S) == '合计':
                    self.ner_arr[i, 0] = TagEnum.total.value
                    self.set_b_relations(i, 0, i, i + 1, 1, self.num_cols, RelEnum.valueIs.value)

    def update_pairs(self):
        for i, j in np.argwhere(self.ner_arr == TagEnum.value.value).tolist():
            rel_value_index = i * self.num_cols + j
            cond1 = self.rel_arr[:, rel_value_index] == RelEnum.valueIs.value
            arg_result = np.argwhere(cond1).tolist()
            if not arg_result:
                continue
            # value 对应一个key
            if len(arg_result) == 1:
                rel_key_index_list = [k[0] for k in arg_result if k]
                for rel_key_index in rel_key_index_list:
                    key_i = int(rel_key_index) // self.num_cols
                    key_j = int(rel_key_index) % self.num_cols
                    self.k_v_pairs[(key_i, key_j)].append((i, j))
            # value 对应多个key
            elif len(arg_result) >= 2:
                rel_key_index_list = [k[0] for k in arg_result if k]
                key_list = []
                for rel_key_index in rel_key_index_list:
                    key_i = int(rel_key_index) // self.num_cols
                    key_j = int(rel_key_index) % self.num_cols
                    key_list.append((key_i, key_j))
                self.ks_v_pairs[tuple(key_list)].append((i, j))

    def pairs_to_record_list(self):
        self.update_pairs()
        data = []
        # k_v_pairs
        d = defaultdict(list)

        for (key_i, key_j), values in self.k_v_pairs.items():
            for (value_i, value_j) in values:
                key_text = self.table_rows[key_i][key_j].text
                if key_text not in self.filterList:
                    value_text = self.table_rows[value_i][value_j].text
                    d[key_text].append(value_text)
        if d:
            min_num = min(len(v) for v in d.values())
            for k, v in d.items():
                d[k] = v[:min_num]
            df = pd.DataFrame(d).fillna('')
            data += df.to_dict(orient='records')
        # ks_v_pairs
        d = {}
        for keys, values in self.ks_v_pairs.items():
            keys = list(keys)
            keys.sort()
            key_text_list = []
            for key_i, key_j in keys:
                key_text = self.table_rows[key_i][key_j].text
                if key_text not in self.filterList:
                    key_text_list.append(key_text)
            key_text = '|'.join(key_text_list)
            if not key_text:
                continue
            if values:
                value_i, value_j = values[0]
                value_text = self.table_rows[value_i][value_j].text
                if value_text not in self.filterList:
                    d[key_text] = value_text
        data.append(d)
        data = [d for d in data if d]
        self.kv_output = data
        return data


class TableOps:

    def __init__(self):
        self.labels = None

    @staticmethod
    def judge_similar_text_list(inp: List[List[str]]):
        if len(inp) < 2:
            return -1
        textList = []
        for inp_ in inp:
            for i in range(len(inp_)):
                inp_[i] = re.sub(r"\s+", "", inp_[i], flags=re.S)
            textList.append('\n'.join([k for k in inp_ if k]))
        numCharsList = [len(k) for k in textList]
        mu = np.mean(numCharsList)
        sigma = np.std(numCharsList)
        if sigma / mu < 0.1:
            return 1
        else:
            return 0

    def table_processing(self, st: SimpleTable):
        num_cols = st.num_cols
        num_rows = st.num_rows
        textList = []
        if num_cols == 2 and num_rows >= 3:
            sens = ['，'.join(st.get_head_list(0, 0))]
            if textList and sens[0] not in textList:
                return False
            tableHeadRecModel = TableHeadService.call(sens)
            self.labels = tableHeadRecModel.labels
            if any(k in st.table_rows[0][0].text for k in ['公司披露年度报告', '统一社会信用代码', '组织机构代码', '会计师事务所']
                   ) or num_rows >= 4:
                st.ner_arr[:, 0] = TagEnum.key.value
                st.set_b2b_relations(0, 1, RelEnum.value_is.value, (0, num_rows), axis=1)
        else:
            sens = ['，'.join(st.get_head_list(0, 0)),
                    '，'.join(st.get_head_list(0, 0))]
            if textList and sens[0] not in textList:
                return False
            tableHeadRecModel = TableHeadService.call(sens)
            self.labels = tableHeadRecModel.labels
            rowno_list = self.judge_row_head(st, num_rows)
            if tableHeadRecModel.labels == [1, 0] or any(k in st.table_rows[0][0].text for k in ['保荐机构名称', '财务顾问', '股东名称']):
                st.ner_arr[0, :] = TagEnum.key.value
                for rowno in range(1, num_rows):
                    st.set_b2b_relations(0, rowno, RelEnum.value_is.value, (0, num_cols), axis=0)
                st.set_total_tag_relations()
            elif tableHeadRecModel.labels == [0, 1]:
                st.ner_arr[:, 0] = TagEnum.key.value

                for colno in range(1, num_cols):
                    st.set_b2b_relations(0, colno, RelEnum.value_is.value, (0, num_rows), axis=1)
                    for rowno in rowno_list:
                        st.set_b2b_relations(0, colno, RelEnum.other.value, (rowno, rowno + 1), axis=1)
                if rowno_list:
                    for rowno in rowno_list:
                        st.ner_arr[rowno, :] = TagEnum.key.value
                    for r1, r2 in zip(rowno_list, rowno_list[1:] + [None]):
                        for rowno in range(r1 + 1, r2 if r2 is not None else num_rows):
                            st.set_b2b_relations(r1, rowno, RelEnum.value_is.value, (1, num_cols), axis=0)
                if len(rowno_list) <= 1:
                    st.set_total_tag_relations()
            elif (tableHeadRecModel.labels == [1, 1] or st.table_rows[0][0].text in st.filterList
                  or st.table_rows[0][0].text == '项目'):
                st.ner_arr[:, 0] = TagEnum.key.value
                if 0 not in rowno_list:
                    rowno_list = [0] + rowno_list
                for colno in range(1, num_cols):
                    st.set_b2b_relations(0, colno, RelEnum.value_is.value, (0, num_rows), axis=1)
                    for rowno in rowno_list:
                        st.set_b2b_relations(0, colno, RelEnum.other.value, (rowno, rowno + 1), axis=1)
                if rowno_list:
                    for rowno in rowno_list:
                        st.ner_arr[rowno, 1:] = TagEnum.key.value
                        st.ner_arr[rowno, 0] = TagEnum.title.value
                    for r1, r2 in zip(rowno_list, rowno_list[1:] + [None]):
                        for rowno in range(r1 + 1, r2 if r2 is not None else num_rows):
                            st.set_b2b_relations(r1, rowno, RelEnum.value_is.value, (1, num_cols), axis=0)
                if len(rowno_list) <= 1:
                    st.set_total_tag_relations()

        return True

    def judge_row_head(self, st, num_rows):
        # 指标类数据横向表头判断 start
        rowno_list = []
        for rowno in range(num_rows):
            res = re.findall(r'\d{4}年.*?，', '，'.join(st.get_head_list(rowno, 0, 1)) + "，")
            if res and len(res) >= 2:
                rowno_list.append(rowno)
        if rowno_list and num_rows // len(rowno_list) <= 2:
            rowno_list = []
        if rowno_list:
            return rowno_list
        for rowno in range(num_rows):
            res = re.findall(r'本报告期.*?，', '，'.join(st.get_head_list(rowno, 0, 1)) + "，")
            if res and len(res) >= 2:
                rowno_list.append(rowno)
        if rowno_list and num_rows // len(rowno_list) <= 2:
            rowno_list = []
        return rowno_list

    def process(self, image_id,
                table_rows: List[List[Tag]],
                bboxes: Optional[List[List[int]]],
                cell_boxes: Optional[List[List[int]]],
                helper: LabelStudioHelper,
                height, width
                ) -> Optional[Union[SimpleTable, ComplexTable]]:
        # if is_simple(table_rows):
        #     st = SimpleTable(image_id, table_rows)
        #     is_done = self.table_processing(st)
        #     if is_done:
        #         data = st.pairs_to_record_list()
        #         if data:
        #             st.has_data = True
        #             logger.warning(f'{image_id} simple and recognized')
        #             # print(image_id + "\n" + json.dumps(data, indent=2, ensure_ascii=False))
        #             return st
        #     logger.warning(f'{image_id} not recognized table')
        #     return st
        # else:
        #     ct = ComplexTable(image_id, table_rows, bboxes)
        #     logger.warning(f'{image_id} complex table')
        #     return ct
        ct = ComplexTable(image_id, table_rows, bboxes, cell_boxes, helper, height, width)
        # print(json.dumps(ct.to_records(), ensure_ascii=False, indent=2))
        return ct
