# -*- coding: utf-8 -*-
# @Time : 2024/3/13 17:05
# @Author : yangyc
import enum
from collections import defaultdict
from pydantic import BaseModel
from typing import List, Union, Optional, Dict
from .xfund_model import XfundDocument, BoundingBox


class TagEnum(enum.IntEnum):
    def __new__(cls, value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    other = 0
    title = 1
    total = 2
    key = 3
    value = 4
    remark = 5
    project = 6


class RelEnum(enum.IntEnum):
    def __new__(cls, value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    other = 0
    valueIs = 1
    belongTo = 2
    aggTo = 3


class MergeTagEnum(enum.IntEnum):
    def __new__(cls, value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    other = 0
    up = 1
    down = 2
    single = 3


class MergeRelEnum(enum.IntEnum):
    def __new__(cls, value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    other = 0
    merge = 1
    unmerge = 2


HEAD_KEYS = [TagEnum.key.value, TagEnum.title.value, TagEnum.project.value, TagEnum.total.value]
ID_TO_TAG: Dict[int, str] = {e.value: e.name for e in TagEnum}
TAG_TO_ID: Dict[str, int] = {e.name.upper(): e.value for e in TagEnum}
REL_ID_TO_TAG: Dict[int, str] = {e.value: e.name for e in RelEnum}
REL_TAG_TO_ID: Dict[str, int] = {e.name.upper(): e.value for e in RelEnum}

MERGE_ID_TO_TAG: Dict[int, str] = {e.value: e.name for e in MergeTagEnum}
MERGE_TAG_TO_ID: Dict[str, int] = {e.name.upper(): e.value for e in MergeTagEnum}
MERGE_REL_ID_TO_TAG: Dict[int, str] = {e.value: e.name for e in MergeRelEnum}
MERGE_REL_TAG_TO_ID: Dict[str, int] = {e.name.upper(): e.value for e in MergeRelEnum}


class TableImage(BaseModel):
    md5: str
    width: int
    height: int


class SubLine(BaseModel):
    pageNumber: int
    box: Optional[List[Union[float, int]]]  # 子文本框坐标x1,y1,x2,y2
    text: str


class SubCell(BaseModel):
    pageNumber: int
    box: Optional[List[Union[float, int]]]  # 子单元格坐标x1,y1,x2,y2


class Cell(BaseModel):
    id: int
    subLines: List[SubLine]  # 多个子文本行
    subCells: Optional[List[SubCell]] = None  # 多个子单元格
    indexBox: Optional[List[int]] = None  # 单元格行号,列号,行号+rowspan,列号+colspan
    box: Optional[List[float]] = None
    labelId: int = TagEnum.other.value


class Relation(BaseModel):
    fromId: int
    toId: int
    labelId: int


class MixImageTextTable(BaseModel):
    id: str
    nRows: int  # 全局行数
    nCols: int  # 全局列数
    tableImages: List[TableImage]  # 图片md5
    cells: List[Cell]
    relations: Optional[List[Relation]] = None

    def to_xfund_2(self, model_name='table_ser'):

        id_to_tag = ID_TO_TAG
        if model_name == 'table_merge':
            id_to_tag = MERGE_ID_TO_TAG
        document = []
        page0 = -1
        for cell in self.cells:
            if cell.subLines:
                page0 = cell.subLines[0].pageNumber
                break
        maxWidth = max(tableImage.width for tableImage in self.tableImages)
        tableImage = self.tableImages[0]
        for cell in self.cells:
            bboxes = []
            if cell.subLines:
                for subLine in cell.subLines:
                    if subLine.box is None:
                        continue
                    offset = subLine.pageNumber - page0 if model_name != 'table_merge' else 0
                    h_offset = sum(self.tableImages[index].height for index in range(offset))
                    bbox = [subLine.box[0], subLine.box[1] + h_offset, min(maxWidth, subLine.box[2]), subLine.box[3] + h_offset]
                    bboxes.append(bbox)

            indexBox = cell.indexBox
            cboxes = []
            if cell.subCells:
                for subCell in cell.subCells:
                    if subCell.box is None:
                        continue
                    offset = subCell.pageNumber - page0 if model_name != 'table_merge' else 0
                    h_offset = sum(self.tableImages[index].height for index in range(offset))
                    cbox = [subCell.box[0], subCell.box[1] + h_offset, min(maxWidth, subCell.box[2]), subCell.box[3] + h_offset]
                    cboxes.append(cbox)
            int_bbox = self.to_int_box(self.merge_bbox(bboxes))
            int_cbox = self.to_int_box(self.merge_bbox(cboxes))
            if not int_bbox and not int_cbox:
                continue
            linking = None
            if self.relations:
                linking = []
                for rel in self.relations:
                    if rel.fromId == cell.id:
                        linking.append([rel.fromId, rel.toId, rel.labelId])
            document.append(BoundingBox(id=cell.id,
                                        text=''.join([line.text for line in cell.subLines]),
                                        label=id_to_tag[cell.labelId],
                                        box=int_bbox,
                                        indexBox=indexBox,
                                        linking=linking
                                        ))
        if not document:
            print(self.id, 'document is empty')
        return XfundDocument(id=self.id,
                             document=document,
                             img={"fname": tableImage.md5,
                                  "width": tableImage.width,
                                  "height": tableImage.height
                                  })

    @staticmethod
    def merge_bbox(box_list):
        if not box_list or any(box is None for box in box_list):
            return None
        x0, y0, x1, y1 = list(zip(*box_list))
        return [min(x0), min(y0), max(x1), max(y1)]

    @staticmethod
    def to_int_box(box):
        return [int(k) for k in box] if box else None

    def to_records(self):
        assert self.cells and self.relations
        self.relations.sort(key=lambda x: (int(x.from_id), int(x.to_id)))
        key2key = {}
        value2key = defaultdict(list)
        records = []
        id2text = {}
        for cell in self.cells:
            text = ''.join([line.text for line in cell.subLines])
            id2text[int(cell.id)] = text
        for relation in self.relations:
            from_id = int(relation.from_id)
            to_id = int(relation.to_id)
            if from_id > to_id:
                from_id, to_id = to_id, from_id
            elif from_id == to_id:
                continue
            a = self.cells[from_id].labelId
            b = self.cells[to_id].labelId
            if relation.label == RelEnum.belongTo.name:
                if a in HEAD_KEYS and b in HEAD_KEYS:
                    key2key[from_id] = to_id
            if relation.label == RelEnum.valueIs.name:
                if a in HEAD_KEYS and b == TagEnum.value.name:
                    value2key[to_id].append(from_id)

        for value_id, key_id_list in sorted(value2key.items(), key=lambda x: (x[0], x[1][0])):
            value = id2text[value_id]
            next_ids_list = []
            for next_id in key_id_list:
                next_ids = [next_id]
                while next_id in key2key:
                    next_id = key2key[next_id]
                    next_ids.append(next_id)
                if next_ids:
                    next_ids_list.append(next_ids)
            key_text_list = []
            for next_ids in next_ids_list:
                next_ids.sort()
                key_text = '|'.join(id2text[key_id] for key_id in next_ids)
                key_text_list.append(key_text)
            records.append({
                '|'.join(key_text_list): id2text[value_id]
            })
        return records
