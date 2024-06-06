# -*- coding: utf-8 -*- 
# @Time : 2024/3/13 17:11 
# @Author : yangyc
import json
import re
import os
import logging
from typing import List
import cv2
import matplotlib.pyplot as plt
from bs4.element import Tag
from parser.abstract import Paragraph
from parser.pdf import Pdf
from service.table_shot_service import TableShot
from service.table_re_service import TableOps, SimpleTable, ComplexTable
from service.labling_service import LabelStudioHelper
from service.pre_labeling_service import PreLabelingHelper
from utils.ac_search import generating_ac, extracting_keyword

TITLE_PATTERNS = [
    re.compile(r'^([一二三四五六七八九十0-9]+[.、]|[(（][一二三四五六七八九十0-9]+[)）]).*')
]

UNIT_PATTERNS = [
    re.compile(r'^(单位|币种)[:：].*'),
    re.compile(r'.*适用.*不适用'),
    re.compile('情况|说明|如下.{0,4}：')
]

table_shot = TableShot()
logger = logging.getLogger(__file__)


def pdf_from_html(html_path) -> Pdf:
    pdf = Pdf()
    pdf.from_pdf_A(html_path)
    return pdf


def pdf_merge_table_title(pdf: Pdf):
    for section in pdf.section_tree_dict.values():
        paragraphs = section.paragraphs
        if paragraphs is None:
            continue
        need_remove = []
        i = 1
        parent = section.parent
        titles = [section.title.strip()]
        while parent:
            if parent.title:
                titles.append(parent.title.strip())
            parent = parent.parent
        titles.reverse()
        title = '->'.join(titles)
        while i < len(paragraphs):
            cur_para = paragraphs[i]
            if cur_para.label == 'table':
                back_i = 1
                need_remove = []
                merge_text_list = []
                while True:
                    if i - back_i < 0 or back_i >= 4 or paragraphs[i - back_i].label == 'table':
                        break
                    prev_para = paragraphs[i - back_i]
                    prev_text = ''.join(prev_para.text.split())
                    if any(p.fullmatch(prev_text) for p in UNIT_PATTERNS):
                        need_remove.append(i - back_i)
                        merge_text_list.append(prev_text)
                    elif any(p.fullmatch(prev_text) for p in TITLE_PATTERNS):
                        need_remove.append(i - back_i)
                        merge_text_list.append(prev_text)
                        break
                    back_i += 1
                merge_text_list.reverse()
                cur_para.text = title + " : " + ' | '.join(merge_text_list)
            i += 1
        new_paragraphs: List[Paragraph] = []
        for i in range(len(paragraphs)):
            if i not in need_remove:
                new_paragraphs.append(paragraphs[i])
        section.paragraphs = new_paragraphs


def pdf_table_re(pdf: Pdf):
    ac_tree = generating_ac([
        '公司信息',
        '联系人和联系方式',
        '基本情况简介',
        '信息披露及备置地点',
        '分季度主要财务指标',
        '主要会计数据和财务指标', '主要会计数据', '主要财务指标',
        '非经常性损益项目',
        '研发投入',
        '境内外会计准则差异',
        '公司控股股东',
        '公司实际控制人及其一致行动人',
        '公司股东数量及持股情况',
        '股份变动情况',
        '持股变化情况',
        '资产表',
        '利润表',
        '负债表',
        '流量表'
    ])
    ocr_data = []
    pdfImageLoader = PdfImageLoader(pdf.md5)
    labelStudioHelper = LabelStudioHelper([
        'labeled/project-1-at-2024-03-30-16-10-74f27181.json',
        'labeled/project-2-at-2024-03-30-15-12-fc0a0371.json']
    )
    demo_output = []
    for sec_id, section in pdf.section_tree_dict.items():
        if sec_id == 'root':
            continue
        paragraphs: List[Paragraph] = section.paragraphs
        for paragraph in paragraphs:
            if paragraph.label == 'table':
                if extracting_keyword(ac_tree, paragraph.text):
                    logger.warning(paragraph.text)
                else:
                    continue

                table_rows: List[List[Tag]] = [k.findAll('td') for k in paragraph.contents()]
                # 从selenium获取单元格级别的图像信息
                image, lines, bboxes, tboxes = table_shot.get_image_lines_bboxes(paragraph.html_str)
                text = ''.join(''.join(lines).split())
                image_id = f'{pdf.md5}_{paragraph.id}'
                if image_id != '426FDE8F27C3C7E9BAC89365DD3C88DA_129':
                    continue
                if pdfImageLoader.find_table(text):
                    res = pdfImageLoader.get_table(text)
                    image, lines, bboxes, tboxes = res
                table_shot.save_image(image_id, image, dir_name='./data/shot')
                # table_shot.draw_bboxes(image_id, image, bboxes)
                st = ComplexTable(image_id, table_rows, bboxes, None,
                                  labelStudioHelper, image.shape[0], image.shape[1])
                print(image_id)
                print(json.dumps(st.to_records(), ensure_ascii=False, indent=2))
                demo_output.append({'title': paragraph.text,
                                    'records': st.to_records()})

                ocr_data.append({'image_id': image_id,
                                 'original_height': image.shape[0],
                                 'original_width': image.shape[1],
                                 'lines': lines,
                                 'bboxes': bboxes,
                                 'tboxes': tboxes,
                                 'st': st,
                                 'is_simple': st.is_simple(table_rows)
                                 })
                # 分类保存后用于标注平台上传
                pdfImageLoader.save_image(image_id, image, suffix='_st' if st.is_simple(table_rows) else '')

    with open(f'demo_{pdf.md5}.json', 'w', encoding='utf-8') as fp:
        json.dump(demo_output, fp, ensure_ascii=False, indent=2)
    return ocr_data


def pdf_tsr(pdf: Pdf, split='train', dataset_path='./data/ha_tsr'):
    ac_tree = generating_ac([
        '公司信息',
        '联系人和联系方式',
        '基本情况简介',
        '信息披露及备置地点',
        '分季度主要财务指标',
        '主要会计数据和财务指标', '主要会计数据', '主要财务指标',
        '非经常性损益项目',
        '研发投入',
        '境内外会计准则差异',
        '公司控股股东',
        '公司实际控制人及其一致行动人',
        '公司股东数量及持股情况',
        '股份变动情况', '持股变化情况'
    ])
    aug_data = []
    for sec_id, section in pdf.section_tree_dict.items():
        if sec_id == 'root':
            continue
        paragraphs: List[Paragraph] = section.paragraphs
        for paragraph in paragraphs:
            if paragraph.label == 'table':
                if extracting_keyword(ac_tree, paragraph.text):
                    logger.warning(paragraph.text)
                else:
                    continue
                # 从selenium获取单元格级别的图像信息
                image_id = f'{pdf.md5}_{paragraph.id}'

                res_v2 = table_shot.get_augment_image_lines_bboxes(paragraph.html_str)
                for name in res_v2.keys():
                    image_v2, lines_v2, bboxes_v2, cboxes_v2, tboxes_v2 = res_v2[name]
                    labels = []
                    for bboxes in bboxes_v2:
                        if bboxes and bboxes[0] is None:
                            continue
                        bbox = table_shot.merge_bbox(bboxes)
                        labels.append([0, bbox[0], bbox[1], bbox[2], bbox[3]])
                    filename = f'./images/{split}/{image_id}_{name}'
                    aug_data.append({
                        'label_path': f'{dataset_path}/labels/{split}/{image_id}_{name}.txt',
                        'image_path': f'{filename}.png',  # 相对路径
                        'labels': labels,
                        'split': split
                    })
                    PdfImageLoader.save_image(filename, image_v2, dataset_path, suffix='')
    return aug_data


class PdfImageLoader:
    def __init__(self, md5):
        self.table_dict = {}
        filename = f'data/pdf_raw/json/{md5}.json'
        if not os.path.exists(filename):
            logger.warning(f'PdfImageLoader:{filename} not exists')
            return
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)

            for index, d in enumerate(data, start=1):
                fname = d['img']['fname']
                image = cv2.imread(f'data/pdf_raw/imgs/{fname}.png')
                lines = []
                bboxes = []
                table_boxes = []
                cells = d['cells']
                for cell in cells:
                    line = ''.join([k['text'] for k in cell['lines']]) if cell['lines'] else ''
                    bbox = self.merge_bbox([k['box'] for k in cell['lines']]) if cell['lines'] else None
                    table_box = cell['table_box']
                    lines.append(line)
                    bboxes.append(bbox)
                    table_boxes.append(table_box)
                text = ''.join(''.join(lines).split())
                self.table_dict[text] = (image, lines, bboxes, table_boxes)

    @staticmethod
    def save_image(image_id, image, dir_name='./data/pdf_shot_1', suffix='_st'):
        dir_name = f'{dir_name}{suffix}'
        os.makedirs(dir_name, exist_ok=True)
        plt.imsave(os.path.join(dir_name, f'{image_id}.png'), image)

    def find_table(self, text):
        return text in self.table_dict

    def get_table(self, text):
        return self.table_dict[text]

    @staticmethod
    def merge_bbox(bbox_list):
        x0, y0, x1, y1 = list(zip(*bbox_list))
        return [min(x0), min(y0), max(x1), max(y1)]


def pdf_pre_labeling(ocr_data, *save_paths):
    helper = PreLabelingHelper(ocr_data)
    counts = helper.pre_labeling(*save_paths)
    logger.warning('saving pre_labeling to {},counts:{}'.format(save_paths[0], counts))


def pdf_labeling(corpus_path_list, train_path, valid_path, ocr_data: List, val_id_list):
    helper = LabelStudioHelper(corpus_path_list)
    train_docs = []
    valid_docs = []
    for d in ocr_data:
        image_id = d['image_id']
        lines = d['lines']
        bboxes = d['bboxes']
        tboxes = d['tboxes']
        if image_id in helper.dic:
            xfundDocument = helper.transfer_label_studio_xfund(image_id, lines, bboxes, tboxes)
            if xfundDocument is None:
                print(image_id)
                continue
            xfund = xfundDocument.dict()
            xfund['img']['width'] = int(xfund['img']['width'])
            xfund['img']['height'] = int(xfund['img']['height'])
            if image_id.split("_")[0] in val_id_list:
                valid_docs.append(xfund)
            else:
                train_docs.append(xfund)
        else:
            print(image_id)

    logger.warning('\nsaving {} documents to {}\n{} documents to {}'.format(
        len(train_docs), train_path,
        len(valid_docs), valid_path))

    with open(valid_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'documents': valid_docs}, ensure_ascii=False, indent=2))
    with open(train_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'documents': train_docs}, ensure_ascii=False, indent=2))

