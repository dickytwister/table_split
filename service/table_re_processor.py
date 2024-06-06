# -*- coding: utf-8 -*- 
# @Time : 2024/2/26 13:32 
# @Author : yangyc
import os
import re
from typing import List, Dict, Union

import numpy as np
import requests
import itertools
import cv2
from bs4 import BeautifulSoup
from selenium import webdriver
from dataclasses import dataclass

TEMPLATE = """<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
</head>
<body>
{}
</body>
</html>"""


@dataclass
class TableInfo:
    title: str
    # (x1,y1,x2,y2)
    title_box: List[float]
    cells: List[str]
    # 同一行关系、同一列关系
    row_rels: np.ndarray
    col_rels: np.ndarray
    # [(x1,y1,x2,y2)]
    cell_boxes: List[List[float]]
    cell_aligns: List[str]
    cell_indents: List[float]


class TableShot:
    def __init__(self):
        # 设置Chrome选项以便截图
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器界面
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")  # 设置窗口大小
        chrome_options.add_argument("--start-maximized")  # 最大化窗口
        chrome_options.add_argument("--disable-dev-shm-usage")  # 解决DevToolsActivePort文件太大的问题
        chrome_options.add_argument("--no-sandbox")  # 解决DevToolsActivePort文件太大的问题
        chrome_options.add_argument("--hide-scrollbars")  # 隐藏滚动条，可能有助于提高截图质量
        self.chrome_options = chrome_options
        os.environ['PATH'] = os.environ['PATH'] + ';' + './opt/'
        self.driver = webdriver.Chrome(options=chrome_options)

    def __call__(self, filename_or_str, output_path):
        if not os.path.exists(filename_or_str):
            text = TEMPLATE.format(filename_or_str)
            filename = 'tmp/tmp.html'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8', ) as f:
                f.write(text)
            html_text = filename_or_str
        else:
            filename = filename_or_str
            with open(filename, 'r', encoding='utf-8', ) as f:
                html_text = f.read()

        self.driver.get(os.path.abspath(filename))
        soup = BeautifulSoup(html_text, 'html.parser')

        body = self.driver.find_element_by_tag_name('body')
        table = self.driver.find_element_by_tag_name('table')
        title1 = self.driver.find_elements_by_tag_name('p')[0]
        title1_rect = title1.rect.copy()
        title1_rect['x'] = 0
        title1_rect['width'] = table.rect['width']
        rows1 = table.find_elements_by_tag_name('tr')
        rows2 = soup.find('table').findAll('tr')
        length = len(table.find_elements_by_tag_name('td'))
        cells: List[str] = []
        # 同一行关系、同一列关系
        row_rels: np.ndarray = np.zeros((length, length))
        col_rels: np.ndarray = np.zeros((length, length))
        cell_rects: List[Dict[str, str]] = []
        cell_aligns: List[str] = []
        cell_indents: List[float] = []

        for i in range(len(rows1)):
            cells1 = rows1[i].find_elements_by_tag_name('td')
            cells2 = rows2[i].findAll('td')
            for j in range(len(cells1)):
                cell1 = cells1[j]
                cell2 = cells2[j]
                cell1_rect = cell1.rect.copy()
                cell1_rect['x'] -= table.rect['x']
                cells.append(cell1.text)
                cell_rects.append(cell1_rect)
                style = cell2.attrs.get('style', '')
                if not style and cell2.findAll('p'):
                    style = cell2.findAll('p')[0].get('style', '')
                align, indent = self.get_align_and_indent(style)
                cell_aligns.append(align)
                cell_indents.append(indent)
        for s1 in range(length):
            for s2 in range(length):
                i1 = s1 // len(rows2)
                j1 = s1 % len(rows2)
                i2 = s2 // len(rows2)
                j2 = s2 % len(rows2)
                row_rels[s1, s2] = int(i1 == i2)
                col_rels[s1, s2] = int(j1 == j2)
        table_info = TableInfo(title1.text, self.rect2box(title1_rect), cells,
                               row_rels, col_rels, [self.rect2box(k) for k in cell_rects],
                               cell_aligns, cell_indents)
        body.screenshot(output_path)
        self.horizon_slice(output_path, table.rect['x'], table.rect['x'] + table.rect['width'])
        print(f'saved screenshot to {output_path}')
        return table_info

    @staticmethod
    def rect2box(rect):
        x = rect['x']
        y = rect['y']
        width = rect['width']
        height = rect['y']
        return [x, y, x + width, y + height]

    @staticmethod
    def horizon_slice(output_path, start, end):
        image = cv2.imread(output_path)  # h,w,c
        image = image[:, int(start):int(end)]
        cv2.imwrite(output_path, image)

    @staticmethod
    def horizon_align(output_path):
        image = cv2.imread(output_path)  # h,w,c
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(img_gray.astype(np.uint8), 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        w_w = [np.count_nonzero(binary[:, i] == 255) for i in range(binary.shape[1])]
        start = 0
        end = len(w_w) - 1
        for i in range(len(w_w)):
            if w_w[i] > 0:
                start = i
                break
        for j in range(len(w_w) - 1, start, -1):
            if w_w[j] > 0:
                end = j
                break
        return start, end

    @staticmethod
    def get_align_and_indent(style):
        style = ''.join(style.split())
        align = 'left'
        indent = 0
        r = re.findall(r'text-align:(left|right|center)', style)
        if r:
            align = r[0]
        r = re.findall(r'text-indent:(\d\.)', style)
        if r:
            indent = float(r[0])

        return align, indent

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


def hs(img_path):
    try:
        url = "http://10.3.12.7:8866/hsnlp/ocr/parse_image?char_position=on"
        # url = 'http://10.3.12.8:9292/gilocr/hsocr/v1?key=text_extract&ocr_service=svtr&char_position=on'
        res = requests.post(url, files={'file': open(img_path, mode='rb')})
        text_content = res.json()['data']['lines_content']
        chars = []
        image = cv2.imread(img_path)
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
        colors = itertools.cycle(colors)
        count = 0
        for cont in text_content:
            color = colors.__next__()
            for info in cont['characters']:
                pos = info['position']
                chars.append((pos[0], pos[2]))
                cv2.rectangle(image, [int(k) for k in pos[0]], [int(k) for k in pos[2]], color=color, thickness=1)
            count += 1

        suffix = img_path.split('/')[-1].split('.')[0]
        filename = f'data/draws/hs_{suffix}.png'
        cv2.imwrite(filename, image)
        print('hsocr line_contents:', filename)
        return text_content
    except Exception as e:
        print('error', e)


class TableForm:
    def __init__(self):
        self.hs_url = ("http://10.3.12.7:6080/ocr/table_detect/unet_gan"
                       "?key=text_extract&detect=True&serve_type=ant_cleaning&orien_class=True")
        self.gil_url = 'http://10.3.12.8:9230/ocr/gilocr/image_extract?key=text_extract'

    def hs_table(self, img_path, output_path):
        res = requests.post(self.hs_url, files={'file': open(img_path, mode='rb')})
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(res.json()['data'])

    def gil_table(self, img_path, output_path):
        res = requests.post(self.gil_url, files={'file': open(img_path, mode='rb')})
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(TEMPLATE.format(res.json()['data']))


@dataclass
class TableAnnotation:
    html_path: str
    image_path: str
    table_info: TableInfo


@dataclass
class TableLineAnnotation(TableAnnotation):
    ocr_results: List[Dict[str, Union[str, List[int]]]]
    content_list: List[str]
    box_list: List[int]
    label_list: List[str]
    row_rels: np.ndarray
    col_rels: np.ndarray
    align_list: List[str] = None
    indent_list: List[int] = None


class TableLabeling:
    def __init__(self):
        self.table_form = TableForm()
        self.table_shot = TableShot()
        self.anno_list: List[TableAnnotation]

    def labeling(self, html_path, image_path) -> TableLineAnnotation:
        show_path = os.path.split(html_path)[1]
        table_info = self.table_shot(html_path, image_path)
        print(show_path, '完成html截图和文本、位置信息提取')
        ocr_results = hs(image_path)
        print(show_path, '完成截图ocr文字坐标提取')
        text_content_list = [table_info.title] + table_info.cells
        text_label_list = ['title'] + ['cell'] * len(table_info.cells)
        text_box_list = [table_info.title_box] + table_info.cell_boxes
        text_row_col_list = [None]
        num_row, num_col = table_info.row_rels.shape[0], table_info.row_rels.shape[1]
        for index in range(num_row * num_col):
            row = index // num_col
            col = index % num_col
            text_row_col_list.append((row, col))
        line_content_list, line_box_list, line_label_list, line_row_rels, line_col_rels = self.text_line_mapping(
            ocr_results, text_box_list, text_row_col_list, text_content_list, text_label_list)
        anno = TableLineAnnotation(html_path, image_path, table_info,
                                   ocr_results, line_content_list,
                                   line_box_list, line_label_list,
                                   line_row_rels, line_col_rels
                                   )
        print(show_path, '完成标注数据生成')
        return anno

    def text_line_mapping(self, text_content, text_box_list, text_row_col_list, text_content_list, text_label_list):
        # labels: cell,title, half_cell, half_title, other
        # rels: true or false
        content_list = [x['text'] for x in text_content]
        box_list = [x['position'][0] + x['position'][2] for x in text_content]
        label_list = ["" for _ in range(len(box_list))]
        iou_arr = np.empty((len(box_list), len(text_box_list)))
        row_rels = np.zeros((len(box_list), len(text_box_list)))
        col_rels = np.zeros((len(box_list), len(text_box_list)))
        for i in range(len(box_list)):
            for k in range(len(text_box_list)):
                box1 = box_list[i]
                box2 = text_box_list[k]
                iou_arr[i, k] = self.calculate_iou(box1, box2)[1]

        for i in range(len(box_list)):
            k = iou_arr[i, :].argmax()
            label_list[i] = text_label_list[k]
            if label_list[i] not in ['cell', 'title']:
                continue
            top_line_box_i_list = -iou_arr[:, k].argsort()[:2]
            if len(top_line_box_i_list) >= 2:
                label_list[i] = 'half_' + label_list[i]

        for i in range(len(box_list)):
            for j in range(len(box_list)):
                k_1 = iou_arr[i, :].argmax()
                k_2 = iou_arr[j, :].argmax()
                if text_row_col_list[k_1] is None or text_row_col_list[k_2] is None:
                    continue
                row_1, col_1 = text_row_col_list[k_1]
                row_2, col_2 = text_row_col_list[k_2]
                if row_1 == row_2 > 0:
                    row_rels[i, j] = 1
                if col_1 == col_2 > 0:
                    col_rels[i, j] = 1
        return content_list, box_list, label_list, row_rels, col_rels

    @staticmethod
    def get_normalized_str(text):
        text = re.sub(r"\s+", "", text, flags=re.S)
        return text

    @staticmethod
    def calculate_area(box):
        x1, y1, x2, y2 = box
        return (x2 - x1) * (y2 - y1)

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

    def augment(self):
        pass


def main():
    html_path = './data/table2image/table1.html'
    image_path = './data/table2image/table1.png'
    anno = TableLabeling().labeling(html_path, image_path)
    print(anno)


if __name__ == '__main__':
    main()
