import os
import json
from copy import deepcopy


def json_add(image_json):
    line = image_json["line"]
    up_cells = []  # 上方单元格
    down_cells = []  # 下方单元格
    # print(line)
    # 遍历所有cells，统计上下方cells
    for cell in image_json["cells"]:
        # print(cell["box"])
        if cell["box"][1] < line - 10 < cell["box"][3]:
            up_cells.append(cell)
        elif cell["box"][1] < line + 10 < cell["box"][3]:
            down_cells.append(cell)
    # print(up_cells)
    # print(down_cells)
    # 统计已经有relation的cells
    skip_cells = []
    for relation in image_json["relations"]:
        if relation["fromId"] not in skip_cells:
            skip_cells.append(relation["fromId"])
        if relation["toId"] not in skip_cells:
            skip_cells.append(relation["toId"])
    # print(skip_cells)
    for up_cell in up_cells:
        if up_cell["id"] in skip_cells:
            continue
        for down_cell in down_cells:
            if down_cell["id"] in skip_cells:
                continue
            # if down_cell["indexBox"][1] == up_cell["indexBox"][1]:
            if ((up_cell["box"][0] - 8 <= down_cell["box"][0] and down_cell["box"][2] <= up_cell["box"][2] + 8)
                    or (down_cell["box"][0] - 8 <= up_cell["box"][0] and up_cell["box"][2] <= down_cell["box"][2] + 8)):
                image_json["relations"].append({
                    "fromId": up_cell["id"],
                    "toId": down_cell["id"],
                    "labelId": 2
                })

    # 根据relations给cells添加labelId
    for relation in image_json["relations"]:
        if relation["labelId"] == 0:
            continue
        elif relation["labelId"] == 1:
            for cell in image_json["cells"]:
                if cell["id"] == relation["fromId"]:
                    cell["labelId"] = 1
                elif cell["id"] == relation["toId"]:
                    cell["labelId"] = 2
        else:
            for cell in image_json["cells"]:
                if cell["id"] == relation["fromId"] or cell["id"] == relation["toId"]:
                    cell["labelId"] = 3


def add_relations(image_json):
    new_image_json = deepcopy(image_json)
    line = new_image_json["line"]
    up_cells = []  # 上方单元格
    down_cells = []  # 下方单元格
    # print(line)
    # 遍历所有cells，统计上下方cells
    for cell in new_image_json["cells"]:
        # print(cell["box"])
        if cell["box"][1] < line - 10 < cell["box"][3]:
            up_cells.append(cell)
        elif cell["box"][1] < line + 10 < cell["box"][3]:
            down_cells.append(cell)
    # print(up_cells)
    # print(down_cells)
    # 统计已经有relation的cells
    skip_cells = []
    for relation in new_image_json["relations"]:
        if relation["fromId"] not in skip_cells:
            skip_cells.append(relation["fromId"])
        if relation["toId"] not in skip_cells:
            skip_cells.append(relation["toId"])
    # print(skip_cells)
    for up_cell in up_cells:
        if up_cell["id"] in skip_cells:
            continue
        for down_cell in down_cells:
            if down_cell["id"] in skip_cells:
                continue
            # if down_cell["indexBox"][1] == up_cell["indexBox"][1]:
            if ((up_cell["box"][0] - 8 <= down_cell["box"][0] and down_cell["box"][2] <= up_cell["box"][2] + 8)
                    or (down_cell["box"][0] - 8 <= up_cell["box"][0] and up_cell["box"][2] <= down_cell["box"][2] + 8)):
                new_image_json["relations"].append({
                    "fromId": up_cell["id"],
                    "toId": down_cell["id"],
                    "labelId": 2
                })

    # 根据relations给cells添加labelId
    for relation in new_image_json["relations"]:
        if relation["labelId"] == 0:
            continue
        elif relation["labelId"] == 1:
            for cell in new_image_json["cells"]:
                if cell["id"] == relation["fromId"]:
                    cell["labelId"] = 1
                elif cell["id"] == relation["toId"]:
                    cell["labelId"] = 2
        else:
            for cell in new_image_json["cells"]:
                if cell["id"] == relation["fromId"] or cell["id"] == relation["toId"]:
                    cell["labelId"] = 3

    return new_image_json


def process_json_file(json_input_path, json_output_path):  # 遍历json_input_path下的所有json文件，并保存到json_output_path下
    for root, dirs, files in os.walk(json_input_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    image_json = json.load(f)
                    new_image_json = add_relations(image_json)
                    new_file_path = os.path.join(json_output_path, file)
                    with open(new_file_path, 'w', encoding='utf-8') as f:
                        json.dump(new_image_json, f, ensure_ascii=False, indent=4)


# 测试
if __name__ == '__main__':
    # json_input_path = "./样例/output2"
    # json_output_path = "./样例/output3"

    json_input_path = "F:/恒生/data/Fund/mix_cut/json"
    json_output_path = "F:/恒生/data/Fund/mix_add_relations/json"

    process_json_file(json_input_path, json_output_path)
