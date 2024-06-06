"""
@author:byc
@created:2024-05-30
@description:
1. 任务背景介绍：
    1）在对跨页表格合并关系的多模态模型的训练任务中，训练数据如果只是通过人工标注产生，会存在训练数据过少的问题，从而导致模型训练的进度缓慢，模型指标提升效果不明显。
    2）本项目提供了一种基于上游提供的标注文件和完整表格图片，自动生成拆分表格数据的方法，从而达到数据扩增的目的。
    3）在训练的过程中通过将生成的扩增数据加入训练集，或将使用扩增数据训练出的模型作为预训练模型，相较于纯人工标注数据训练结果，使用这两种数据扩增方法进行训练，模型指标都有2%左右的提升。
2. 主要任务流程
    1）生成mix格式文件，包括去掉首尾的画线
    2）根据所画的线对图片和json文件进行裁剪并输出
    3）对生成的json文件补充没有合并关系单元格的标注
    4）根据json文件生成xfund标注格式文件
    5）将xfund标注文件中相互关联的单元格放在一起，无法匹配的document从文件中删除
"""
import os
import json
from pathlib import Path
import argparse
from PIL import Image
from xfund_transfer_labeled_data_v3 import load_xfund_object
from utils.mix_generate3 import new_json
from utils.mix_cut import cut_mix
from utils.add_relations_labelid import json_add
from utils.json_replace import json_replace

from utils.get_line_box import get_horizontal_lines_box
from utils.get_line_text import get_horizontal_lines_text



def table_split(json_folder, image_folder, image_output_folder, json_output_folder):
    # 遍历 JSON 文件夹中的所有 JSON 文件
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)
            # 读取 JSON 文件
            # print(json_path)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for pic_num in range(2):
                    # 获取表格图片的信息
                    image_json = data['tableLabelList'][pic_num].copy()
                    # print(image_json)
                    image_name = image_json['tableImages'][0]['md5']
                    image_path = os.path.join(image_folder, image_name)
                    # 获取要画的线
                    lines_box = get_horizontal_lines_box(data, image_folder, pic_num)
                    lines_text = get_horizontal_lines_text(data, image_folder, pic_num)
                    if not lines_box and not lines_text:
                        continue
                    elif lines_box and lines_text:
                        lines = lines_box + lines_text
                    elif lines_box and not lines_text:
                        lines = lines_box
                    else:
                        lines = lines_text

                    # print(lines)
                    if not lines or lines == [] or len(lines) < 5:
                        continue
                    lines.sort()
                    # if len(lines) > 1:
                    #     lines.pop()
                    # 对lines进行清洗去除相近的线
                    clean_id = []
                    for i in range(len(lines) - 1):
                        if lines[i + 1] - lines[i] < 10:
                            clean_id.append(i + 1)
                    for i in range(len(clean_id)):
                        del lines[clean_id[i] - i]

                    if not lines or lines == [] or len(lines) < 5:
                        continue

                    for i in range(2, len(lines) - 2):
                        # 根据每条line生成一张新图片和新的json文件
                        # 生成新的json
                        new_image_json = new_json(image_json, lines[i], i)
                        img = Image.open(image_path)
                        # 画线
                        # draw = ImageDraw.Draw(img)
                        # draw.line([(0, lines[i]), (img.width, lines[i])], fill='red', width=2)
                        # 裁剪
                        img = cut_mix(new_image_json, img)
                        # 增加关系
                        json_add(new_image_json)

                        # 将新的json保存到json_output_folder中
                        name, ext = os.path.splitext(image_name)
                        output_name = f"{name}_{i}.json"
                        # output_image = f"{name}_{i}.png"
                        output_path = os.path.join(json_output_folder, output_name)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(new_image_json, f, ensure_ascii=False, indent=4)

                        # 生成新的图片
                        # 保存绘制后的图像到输出文件夹
                        name, ext = os.path.splitext(image_name)
                        output_name = f"{name}_{i}{ext}"
                        output_path = os.path.join(image_output_folder, output_name)
                        img.save(output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument("--image_folder", type=str, default="", help='图片源文件')
    parser.add_argument("--json_folder", type=str, default="", help='json源文件')
    parser.add_argument("--image_output_folder", type=str, default="", help='图片输出文件夹')
    parser.add_argument("--json_output_folder", type=str, default="", help='json输出文件夹')
    parser.add_argument("--xfund_output_folder", type=str, default="", help='xfund标注文件生成文件夹')
    args = parser.parse_args()

    table_split(args.json_folder, args.image_folder, args.image_output_folder, args.json_output_folder)
    xfund_json = load_xfund_object(args.json_output_folder)
    xfund_json = json_replace(xfund_json)
    args.xfund_output_folder = Path(args.xfund_output_folder)
    output_path = os.path.join(args.xfund_output_folder, 'tablemerge.train.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(xfund_json, f, ensure_ascii=False, indent=4)
