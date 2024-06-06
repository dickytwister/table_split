from PIL import Image, ImageDraw
import json
import os
from copy import deepcopy
from utils.get_line_box import get_horizontal_lines_box
from utils.get_line_text import get_horizontal_lines_text


def new_json(image_json, line, i):  # 根据line产生新的json
    new_image_json = deepcopy(image_json)
    new_indexbox_0 = 0
    max_id = 0
    new_image_json["relations"] = []  # 添加一个relations字段，记录拆分表格关系
    new_image_json["line"] = line
    # 更改new_image_json的md5字段
    name, ext = os.path.splitext(new_image_json['tableImages'][0]['md5'])
    new_image_json['tableImages'][0]['md5'] = f"{name}_{i}.png"
    # print(new_image_json['tableImages'][0]['md5'])
    # 遍历new_image_json cells中的每个box
    for i in range(len(new_image_json['cells'])):
        # print(new_image_json['cells'][i]['box'])
        # print(new_image_json['cells'][i]['indexBox'])
        # 如果line=box的y2值，记录该cell的indexbox的y2值
        if line == new_image_json['cells'][i]['box'][3] and not new_indexbox_0:
            new_indexbox_0 = new_image_json['cells'][i]['indexBox'][2]
            # print('new_indexbox_0:', new_indexbox_0)
        max_id = max(max_id, new_image_json['cells'][i]['id'])

    if not new_indexbox_0:  # 如果line不属于box的边界
        new_indexbox_line_0 = 0  # 找到线穿过的cells中最大的indexbox[0]
        # new_indexbox_line_2 = 0  # 找到线穿过的cells中最大的indexbox[2]
        for cell in new_image_json['cells']:
            if cell["box"][1] < line < cell["box"][3]:
                new_indexbox_line_0 = max(new_indexbox_line_0, cell["indexBox"][0])
            # if cell["box"][1] < line < cell["box"][3]:
            #     new_indexbox_line_2 = max(new_indexbox_line_2, cell["indexBox"][2])

        # print('new_indexbox_line_0:', new_indexbox_line_0)
        for i in range(len(new_image_json['cells'])):
            # 如果line穿过了当前cell的box，则修改当前cell的box值和indexbox的值
            if new_image_json['cells'][i]['box'][1] < line < new_image_json['cells'][i]['box'][3]:
                new_box_y2 = new_image_json['cells'][i]['box'][3]
                new_image_json['cells'][i]['box'][3] = line
                new_indexbox_2 = new_image_json['cells'][i]['indexBox'][2]  # 取原本的下边indexbox
                new_image_json['cells'][i]['indexBox'][2] = new_indexbox_line_0 + 1
                # 在new_image_json中添加一个新的cell
                new_image_json['cells'].append({
                    "box": [new_image_json['cells'][i]['box'][0], line, new_image_json['cells'][i]['box'][2],
                            new_box_y2],
                    "id": max_id + 1,
                    "indexBox": [new_indexbox_line_0, new_image_json['cells'][i]['indexBox'][1],
                                 # 此时新cell indexbox的y坐标还未+1
                                 new_indexbox_2, new_image_json['cells'][i]['indexBox'][3]],
                    # 创建一个空的subLines列表
                    "subLines": []
                })
                # 更新max_id
                max_id += 1

                # 创建一个空列表来存储满足条件的subline
                matching_sublines = []

                # 遍历new_image_json['cells'][i]['subLines']中的每个subline
                for subline in new_image_json['cells'][i]['subLines']:
                    if (
                            # 限定x轴范围会导致一些subline框在box外的subline被误判
                            # subline['box'][0] > new_image_json['cells'][-1]['box'][0] and
                            # subline['box'][2] < new_image_json['cells'][-1]['box'][2] and
                            subline['box'][1] > new_image_json['cells'][-1]['box'][1] - 8 and
                            subline['box'][3] < new_image_json['cells'][-1]['box'][3] + 8):
                        # 将满足条件的subline添加到matching_sublines列表
                        matching_sublines.append(subline)

                # 在循环结束后，将满足条件的subline移动到image_json['cells'][-1]['subLines']
                for subline in matching_sublines:
                    new_image_json['cells'][-1]['subLines'].append(subline)

                # 从new_image_json['cells'][i]['subLines']中移除这些subline
                for subline in matching_sublines:
                    new_image_json['cells'][i]['subLines'].remove(subline)

                # 向relations中添加关系
                if new_image_json['cells'][i]['subLines'] and new_image_json['cells'][-1]['subLines']:
                    new_image_json['relations'].append({
                        "fromId": new_image_json['cells'][i]['id'],
                        "toId": max_id,
                        "labelId": 1
                    })
                else:
                    new_image_json['relations'].append({
                        "fromId": new_image_json['cells'][i]['id'],
                        "toId": max_id,
                        "labelId": 0
                    })

        # 更新line以下的所有cells的indexbox[0]和indexbox[2]
        for i in range(len(new_image_json['cells'])):
            if new_image_json['cells'][i]['box'][1] >= line:
                new_image_json['cells'][i]['indexBox'][0] += 1
                new_image_json['cells'][i]['indexBox'][2] += 1

        return new_image_json

    for i in range(len(new_image_json['cells'])):
        # 如果line穿过了当前cell的box，则修改当前cell的box值和indexbox的值
        if new_image_json['cells'][i]['box'][1] < line < new_image_json['cells'][i]['box'][3]:
            new_box_y2 = new_image_json['cells'][i]['box'][3]
            new_image_json['cells'][i]['box'][3] = line
            new_indexbox_2 = new_image_json['cells'][i]['indexBox'][2]
            new_image_json['cells'][i]['indexBox'][2] = new_indexbox_0
            # 在new_image_json中添加一个新的cell
            new_image_json['cells'].append({
                "box": [new_image_json['cells'][i]['box'][0], line, new_image_json['cells'][i]['box'][2], new_box_y2],
                "id": max_id + 1,
                "indexBox": [new_indexbox_0, new_image_json['cells'][i]['indexBox'][1],
                             new_indexbox_2, new_image_json['cells'][i]['indexBox'][3]],
                # 创建一个空的subLines列表
                "subLines": []
            })
            # 更新max_id
            max_id += 1

            # 创建一个空列表来存储满足条件的subline
            matching_sublines = []

            # 遍历new_image_json['cells'][i]['subLines']中的每个subline
            for subline in new_image_json['cells'][i]['subLines']:
                if (
                        # 限定x轴范围会导致一些subline框在box外的subline被误判
                        # subline['box'][0] > new_image_json['cells'][-1]['box'][0] and
                        # subline['box'][2] < new_image_json['cells'][-1]['box'][2] and
                        subline['box'][1] > new_image_json['cells'][-1]['box'][1] - 8 and
                        subline['box'][3] < new_image_json['cells'][-1]['box'][3] + 8):
                    # 将满足条件的subline添加到matching_sublines列表
                    matching_sublines.append(subline)

            # 在循环结束后，将满足条件的subline移动到image_json['cells'][-1]['subLines']
            for subline in matching_sublines:
                new_image_json['cells'][-1]['subLines'].append(subline)

            # 从new_image_json['cells'][i]['subLines']中移除这些subline
            for subline in matching_sublines:
                new_image_json['cells'][i]['subLines'].remove(subline)

            # 向relations中添加关系
            if new_image_json['cells'][i]['subLines'] and new_image_json['cells'][-1]['subLines']:
                new_image_json['relations'].append({
                    "fromId": new_image_json['cells'][i]['id'],
                    "toId": max_id,
                    "labelId": 1
                })
            else:
                new_image_json['relations'].append({
                    "fromId": new_image_json['cells'][i]['id'],
                    "toId": max_id,
                    "labelId": 0
                })

    return new_image_json


def process_json_files(json_folder, image_folder, image_output_folder, json_output_folder):
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
                    # 获取要画的线,
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
                        # print(lines[i])
                        # if not new_image_json:  # 如果line不属于box的边界，则进入下一循环
                        #     continue
                        # 将新的json保存到json_output_folder中
                        name, ext = os.path.splitext(image_name)
                        output_name = f"{name}_{i}.json"
                        # output_image = f"{name}_{i}.png"
                        output_path = os.path.join(json_output_folder, output_name)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(new_image_json, f, ensure_ascii=False, indent=4)

                        # 生成新的图片
                        img = Image.open(image_path)
                        # 画线
                        # draw = ImageDraw.Draw(img)
                        # draw.line([(0, lines[i]), (img.width, lines[i])], fill='red', width=2)
                        # 保存绘制后的图像到输出文件夹
                        name, ext = os.path.splitext(image_name)
                        output_name = f"{name}_{i}{ext}"
                        output_path = os.path.join(image_output_folder, output_name)
                        img.save(output_path)


if __name__ == "__main__":
    # json_folder = './样例'
    # image_folder = './样例'
    # image_output_folder = './样例/output'
    # json_output_folder = './样例/output'

    json_folder = 'F:/恒生/original_data/Fund/json'
    image_folder = 'F:/恒生/original_data/Fund/imgs'
    image_output_folder = 'F:/恒生/data/Fund/mix_generate/images'
    json_output_folder = 'F:/恒生/data/Fund/mix_generate/json'

    process_json_files(json_folder, image_folder, image_output_folder, json_output_folder)
