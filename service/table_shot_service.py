# -*- coding: utf-8 -*- 
# @Time : 2024/3/14 18:44 
# @Author : yangyc
import copy
import itertools
import os
import logging
import re

import numpy as np
from typing import List, Dict
import cv2
from selenium import webdriver
import matplotlib.pyplot as plt
from selenium.webdriver.common.by import By

logger = logging.getLogger()
STYLE = """<style>
table {border-collapse: collapse;display: inline-block;table-layout: fixed;}    
th, td {border: 1px solid black;word-wrap: break-word;word-break: break-all;}    
table tr:nth-child(odd) {background-color: #f5f5f5;}    
table tr:nth-child(even) {background-color: #ffffff;}    
table[wellformed="false"] td {border: 1px solid red;}
</style>"""

STYLE_NEW = """<style>
table {border-collapse: collapse;display: inline-block;table-layout: fixed;}    
th, td {border: 1px solid black;word-wrap: break-word;word-break: break-all;}    
table tr:nth-child(odd) {background-color: #ffffff;}    
table tr:nth-child(even) {background-color: #ffffff;}    
table[wellformed="false"] td {border: 1px solid red;}
</style>"""

STYLE_WIRELESS = """<style>
table {border: 0px solid black;border-collapse: collapse;display: inline-block;table-layout: fixed;}    
th, td {border: 0px solid black;word-wrap: break-word;word-break: break-all;}    
table tr:nth-child(odd) {background-color: #ffffff;}    
table tr:nth-child(even) {background-color: #ffffff;}    
table[wellformed="false"] td {border: 1px solid red;}
</style>"""

STYLE_HALF_WIRELESS = """<style>
table {border: 1px solid black;border-collapse: collapse;display: inline-block;table-layout: fixed;}    
th, td {border: 0px solid black;word-wrap: break-word;word-break: break-all;}    
table tr:nth-child(odd) {background-color: #ffffff;}    
table tr:nth-child(even) {background-color: #ffffff;}    
table[wellformed="false"] td {border: 1px solid red;}
</style>"""

TEMPLATE = """<!DOCTYPE html
PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8"/>
</head>
%s
<body>
%s
</body>
</html>"""


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

    def get_image_lines_bboxes(self, filename_or_str):
        table, image = self.get_table_image(filename_or_str, adjust=False)
        lines, bboxes, tboxes = self.get_lines_bboxes(table)
        return image, lines, bboxes, tboxes

    def get_augment_image_lines_bboxes(self, filename_or_str):
        res_v2 = {}
        for name, style in zip(['wire', 'wireless', 'half_wireless'],
                               [STYLE_NEW, STYLE_WIRELESS, STYLE_HALF_WIRELESS]
                               ):
            table, image_v2 = self.get_table_image(filename_or_str, style=style, adjust=True)
            lines_v2, bboxes_v2, cboxes_v2, tboxes_v2 = self.get_lines_bboxes_v2(table)
            res_v2[name] = image_v2, lines_v2, bboxes_v2, cboxes_v2, tboxes_v2
        return res_v2

    def get_table_image(self, filename_or_str, style=STYLE, adjust=False):
        if not os.path.exists(filename_or_str):
            text = TEMPLATE % (style, filename_or_str)
            filename = './tmp/tmp.html'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8', ) as f:
                f.write(text)
        else:
            filename = filename_or_str
        self.driver.get(os.path.abspath(filename))
        table = self.driver.find_element(By.TAG_NAME, 'table')
        # if adjust:
        #     self.adjust_width(table)
        image = cv2.imdecode(np.frombuffer(table.screenshot_as_png, dtype=np.uint8), cv2.IMREAD_COLOR)
        return table, image
    @staticmethod
    def cal_char_num(chars):
        FULL_CODES = [12288] + list(range(65281, 65375))
        count = 0
        for char in chars:
            if ord(char) in FULL_CODES:
                count += 1
            else:
                count += 0.5
        return count

    def adjust_width(self, table):
        """动态调整单元格宽度"""
        ratio_dict = {}
        cells = table.find_elements(By.TAG_NAME, 'td')
        height_list = []
        for cell in cells:
            li = []
            for span in cell.find_elements(By.TAG_NAME, 'span'):
                li.append(span.rect['height'])
            height_list.append(min(li))
        height = np.percentile(height_list, 75)
        char_width = 0
        FULL_CODES = [12288] + list(range(65281, 65375))
        for cell in cells:
            for span in cell.find_elements(By.TAG_NAME, 'span'):
                if span.rect['height'] < height * 1.5 and len(span.text) >=4:
                    count = self.cal_char_num(span.text)
                    char_width = span.rect['width'] / count
                    break

        for i in range(len(cells)):
            cell = cells[i]
            width0 = cell.rect['width']
            spans = cell.find_elements(By.TAG_NAME, 'span')
            text_list = [span.text for span in spans]
            if len(spans) >= 1:
                flag = False
                for a, b in zip(spans, spans[1:]):
                    if a.rect['height'] > height * 1.5:
                        flag = True
                        if b.rect['y'] <= a.rect['y'] + a.rect['height']:
                            delta = spans[1].rect['x'] - spans[0].rect['x']
                            if delta > 0:
                                width = width0 + delta
                                ratio_dict[i] = width / width0
                                break
                if flag and i not in ratio_dict:
                    chars_num = self.cal_char_num(spans[0].text)
                    ratio_dict[i] = 16 * len(spans[0].text) / spans[0].rect['width']

        if ratio_dict:
            max_ratio = max(k for k in ratio_dict.values() if k)
            width = round(float(table.get_attribute("style").split('width:')[1].split('px;')[0]) * max_ratio, 3)
            self.driver.execute_script(f"arguments[0].style.width = '{width}px'", table)
            for i, ratio in ratio_dict.items():
                ratio = ratio if ratio else max_ratio
                cell = cells[i]
                print(cell.text, ratio)
                width = round(float(cell.get_attribute("style").split('width:')[1].split('px;')[0]) * ratio, 3)
                self.driver.execute_script(f"arguments[0].style.width = '{width}px'", cell)
            logger.info('finished adjust width')

    def get_lines_bboxes(self, table):
        lines = []
        bboxes: List[List[float]] = []
        rows = table.find_elements(By.TAG_NAME, 'tr')
        table_rows = []
        for tr in rows:
            table_row = []
            for td in tr.find_elements(By.TAG_NAME, 'td'):
                table_row.append(td)
            table_rows.append(table_row)
        tboxes = self.get_table_boxes(table_rows)
        for i in range(len(table_rows)):
            tr = table_rows[i]
            for j in range(len(tr)):
                cell1 = tr[j]
                lines.append(cell1.text)
                spans = cell1.find_elements(By.TAG_NAME, 'span')
                if not spans:
                    cell1_rect = copy.deepcopy(cell1.rect)
                    cell1_rect['x'] -= table.rect['x']
                    cell1_rect['y'] -= table.rect['y']
                    bboxes.append(self.rect2box(cell1_rect))
                elif len(spans) == 1:
                    cell1_rect = copy.deepcopy(spans[0].rect)
                    cell1_rect['x'] -= table.rect['x']
                    cell1_rect['y'] -= table.rect['y']
                    bboxes.append(self.rect2box(cell1_rect))
                else:
                    bbox_list = []
                    for span in spans:
                        cell1_rect = copy.deepcopy(span.rect)
                        cell1_rect['x'] -= table.rect['x']
                        cell1_rect['y'] -= table.rect['y']
                        bbox = self.rect2box(cell1_rect)
                        bbox_list.append(bbox)
                    bboxes.append(self.merge_bbox(bbox_list))

        return lines, bboxes, tboxes

    def get_lines_bboxes_v2(self, table):
        rows = table.find_elements(By.TAG_NAME, 'tr')
        table_rows = []
        for tr in rows:
            table_row = []
            for td in tr.find_elements(By.TAG_NAME, 'td'):
                table_row.append(td)
            table_rows.append(table_row)
        # 表格行号列号坐标
        tboxes_v2 = self.get_table_boxes(table_rows)
        # 单元格坐标
        cboxes_v2: List[List[float]] = []
        # 单元格的文本行列表
        lines_v2: List[List[str]] = []
        # 单元格的文本框列表
        bboxes_v2: List[List[List[float]]] = []
        for i in range(len(table_rows)):
            tr = table_rows[i]
            for j in range(len(tr)):
                cell1 = tr[j]
                cell1_rect = copy.deepcopy(cell1.rect)
                cell1_rect['x'] -= table.rect['x']
                cell1_rect['y'] -= table.rect['y']
                cboxes_v2.append(self.rect2box(cell1_rect))

                lines = []
                bboxes = []
                spans = cell1.find_elements(By.TAG_NAME, 'span')
                if not spans:
                    lines.append('')
                    bboxes.append(None)
                else:
                    for span in spans:
                        cell1_rect = copy.deepcopy(span.rect)
                        cell1_rect['x'] -= table.rect['x']
                        cell1_rect['y'] -= table.rect['y']
                        bbox = self.rect2box(cell1_rect)
                        lines.append(span.text)
                        bboxes.append(bbox)
                lines_v2.append(lines)
                bboxes_v2.append(bboxes)

        return lines_v2, bboxes_v2, cboxes_v2, tboxes_v2

    @staticmethod
    def merge_bbox(bbox_list):
        x0, y0, x1, y1 = list(zip(*bbox_list))
        return [min(x0), min(y0), max(x1), max(y1)]

    @staticmethod
    def get_table_boxes(table_rows: List):
        """
        获取行号和列号构成的坐标
        :param table_rows:
        :return:
        """
        table_boxes = []
        cols_list = []
        for row in table_rows:
            s = 0
            for cell in row:
                s += int(cell.get_attribute('colspan') or 1)
            cols_list.append(s)
        num_cols = max(cols_list)
        table_arr = np.zeros((1, num_cols))
        cell_id = 0
        index = 0
        for i in range(len(table_rows)):
            col_start = 0
            for j in range(len(table_rows[i])):
                cell = table_rows[i][j]
                row_span = int(cell.get_attribute('rowspan') or 1)
                col_span = int(cell.get_attribute('colspan') or 1)
                if i != len(table_rows) - 1 and i + row_span + 1 > len(table_arr):
                    for k in range(len(table_arr), i + row_span + 1):
                        table_arr = np.concatenate([table_arr, np.zeros((1, num_cols))], axis=0)

                while col_start < num_cols and table_arr[i][col_start] != 0:
                    col_start += 1
                if col_start == num_cols and table_arr[i][col_start] == 1:
                    print('parse error')
                table_arr[i: i + row_span, col_start: col_start + col_span] = cell_id

                table_boxes.append([i, col_start, i + row_span, col_start + col_span])
                index += 1
                cell_id += 1

        return table_boxes

    @staticmethod
    def save_image(image_id, image, dir_name='', suffix='_st'):
        if not dir_name:
            plt.imsave(os.path.join(f'./data/shot{suffix}', f'{image_id}.png'), image)
        else:
            plt.imsave(os.path.join(dir_name, f'{image_id}.png'), image)

    @staticmethod
    def draw_bboxes(image_id, image, bboxes):
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
        colors = itertools.cycle(colors)
        count = 0
        for bbox in bboxes:
            if bbox is None:
                continue
            color = colors.__next__()
            bbox = list(map(int, bbox))
            cv2.rectangle(image, bbox[0:2], bbox[2:4], color=color, thickness=1)
            count += 1
        filename = f'data/draw/{image_id}.png'
        cv2.imwrite(filename, image)

    @staticmethod
    def rect2box(rect):
        x = rect['x']
        y = rect['y']
        width = rect['width']
        height = rect['height']
        return [x, y, x + width, y + height]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()


if __name__ == '__main__':
    table_shot = TableShot()
    filestr = open('tmp/tmp.txt', encoding='utf-8').read()
    _, image = table_shot.get_table_image(filestr, adjust=False)
    table_shot.save_image('000', image)
    _, image = table_shot.get_table_image(filestr, adjust=True)
    table_shot.save_image('001', image)
