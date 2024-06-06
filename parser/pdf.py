# -*- coding: utf-8 -*- 
# @Time : 2024/3/13 10:03 
# @Author : yangyc
import os.path
from typing import List, Dict
from dataclasses import dataclass

from bs4 import BeautifulSoup
from bs4.element import Tag
from parser.abstract import list_to_section_tree, SectionNode, Section, Paragraph


@dataclass
class Pdf:
    md5: str = ""
    title: str = ""
    section_tree_dict: Dict[str, SectionNode] = None
    pdf_page: Tag = None

    def from_pdf_A(self, html_path: str):
        self.md5 = os.path.split(html_path)[-1].split("_")[0]
        html = self.read_file(html_path)
        soup = BeautifulSoup(html, 'html.parser')
        self.title = soup.findAll('p', class_='title')[0].text
        side_bars: List[Tag] = soup.findAll('aside')[0].findAll('li')
        pdf_page: Tag = soup.findAll('div', class_='pdf-page')[0]
        pdf_paras = self.get_pdf_paras(pdf_page)
        pdf_paras_index = {k.get('id'): index for index, k in enumerate(pdf_paras)}
        section_list: List[Section] = []
        for bar, next_bar in zip(side_bars, side_bars[1:] + [None]):
            section_id = bar.findChild().get('id')
            next_section_id = next_bar.findChild().get('id') if next_bar else None
            data_level = int(bar.get('data-level'))
            title = bar.text
            paragraphs = self.get_paras_by_offset(pdf_paras,
                                                  pdf_paras_index,
                                                  section_id,
                                                  next_section_id)
            section = Section(section_id, data_level, title, paragraphs)
            section_list.append(section)
        self.section_tree_dict = list_to_section_tree(section_list)

    @staticmethod
    def get_pdf_paras(pdf_page: Tag) -> List[Tag]:
        paras = {}
        for tag in pdf_page.findAll():
            if tag.has_attr('id'):
                tag_set = set(tag.parent.get('class')) if tag.parent.get('class') else set()
                if tag_set & {'pdf-page-wrapper', 'table-container'}:
                    id = tag.get('id')
                    paras[id] = tag
        return list(paras.values())

    @staticmethod
    def get_paras_by_offset(paras: List[Tag],
                            paras_index: Dict[str, int],
                            start_id: str,
                            end_id: str) -> List[Paragraph]:

        paragraphs: List[Paragraph] = []
        para_start_id = paras_index[start_id.split("_")[0]]
        if end_id:
            para_end_id = paras_index[end_id.split("_")[0]]
            tags: List[Tag] = paras[para_start_id: para_end_id]
        else:
            tags: List[Tag] = paras[para_start_id:]
        for tag in tags:
            para_id: str = tag.get('id')
            label: str = 'table' if tag.name == 'table' else 'text'
            text: str = '' if tag.name == 'table' else tag.text
            paragraphs.append(Paragraph(para_id, label, text, tag))
        return paragraphs

    @staticmethod
    def read_file(file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
