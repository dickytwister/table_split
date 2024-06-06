# -*- coding: utf-8 -*-
# @Time : 2024/3/13 17:05
# @Author : yangyc
# label studio
from pydantic import BaseModel
from typing import List
from .re_model import TagEnum


class BoxValue(BaseModel):
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0
    rectanglelabels: List[str] = [TagEnum.value.name]


class AnnoRelation(BaseModel):
    from_id: str
    to_id: str
    labels: List[str]
    type: str = 'relation'
    direction: str = 'right'


class AnnoBox(BaseModel):
    id: str
    original_width: int
    original_height: int
    value: BoxValue
    from_name: str = 'label'
    to_name: str = 'image'
    type: str = 'rectanglelabels'
    origin: str = 'manual'
    image_rotation: float = 0
