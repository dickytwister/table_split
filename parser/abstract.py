# -*- coding: utf-8 -*- 
# @Time : 2024/3/13 11:09 
# @Author : yangyc
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import Tag


@dataclass
class Paragraph:
    id: str = ""
    label: str = ""
    text: str = ""
    bs_tag: Tag = None
    ods_table: object = None

    def __repr__(self):
        li = [self.id, self.label, self.text]

        return ':'.join([k for k in li if k])

    @property
    def html_str(self):
        return self.bs_tag.decode() if self.bs_tag else None

    def contents(self):
        return self.bs_tag.contents if self.bs_tag else []


@dataclass
class Section:
    id: str = ''
    data_level: int = -1
    title: str = ''
    paragraphs: List[Paragraph] = None

    def __repr__(self):
        return self.title


@dataclass
class SectionNode(Section):
    children: List = None
    parent = None

    def __repr__(self):
        return self.title


def list_to_section_tree(sections: List[Section]) -> Dict[str, SectionNode]:
    section_tree_dict = {}
    root = SectionNode(children=[])
    section_tree_dict['root'] = root
    parent_dict: Optional[Dict[int, SectionNode]] = {}
    last_node = None
    for section in sections:
        data_level = section.data_level
        node = SectionNode(section.id,
                           section.data_level,
                           section.title,
                           section.paragraphs,
                           [])
        section_tree_dict[section.id] = node
        if last_node is None:
            parent_dict[data_level] = root
            node.parent = root
            root.children.append(node)
        else:
            if data_level > last_node.data_level:
                last_node.children.append(node)
                node.parent = last_node
                parent_dict[data_level] = last_node
            else:
                for intvalue in range(data_level, -1, -1):
                    if intvalue in parent_dict:
                        parent_dict[intvalue].children.append(node)
                        node.parent = parent_dict[intvalue]
                        break
        last_node = node

    return section_tree_dict
