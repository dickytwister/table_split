# -*- coding: utf-8 -*-
# @Time : 2024/3/13 17:05
# @Author : yangyc
# xfund dataset
from pydantic import BaseModel
from typing import List, Optional, Dict, Union


class BoundingBox(BaseModel):
    id: int
    text: str
    label: str
    box: Optional[List[int]]
    indexBox: Optional[List[int]] = None
    linking: Optional[List[List[int]]] = None


class XfundDocument(BaseModel):
    """
    for xfund dataset
    """
    id: str
    document: List[BoundingBox]
    img: Dict[str, Union[str, int]]
