from PIL import Image
import json
import os
from copy import deepcopy


def cut_mix(image_json, image):
    line = image_json["line"]
    # print(line)
    # 定义上下裁切的线段
    up_line, low_line = line, line
    index_cut_up = 0
    # 遍历cells中的box，找到和line相接的cells的最高坐标和最低坐标
    for cell in image_json["cells"]:
        if line - 15 < cell["box"][3] < line + 15:  # 如果当前cell的下边界与line相接
            if cell["box"][1] < up_line:  # 如果当前cell的上边界高于up_line
                up_line = cell["box"][1]  # 更新up_line
                index_cut_up = cell["indexBox"][0]  # 更新上部要被切去的索引
        if line - 15 < cell["box"][1] < line + 15:
            if cell["box"][3] > low_line:  # 如果当前cell的下边界低于low_line
                low_line = cell["box"][3]  # 更新low_line
    # 遍历cells中的box，移除up_line之上的box和low_line之下的box，并更新其余box的坐标和indexBox
    image_json["line"] -= up_line
    remove_list = []
    for cell in image_json["cells"]:
        if cell["box"][3] < up_line + 8:  # 如果当前cell的下边界高于up_line
            remove_list.append(cell["id"])
        elif cell["box"][1] > low_line - 8:  # 如果当前cell的上边界低于low_line
            remove_list.append(cell["id"])
        else:  # 其余要保留的cell
            cell["box"][1] = cell["box"][1] - up_line
            cell["box"][3] = cell["box"][3] - up_line
            cell["indexBox"][0] = cell["indexBox"][0] - index_cut_up
            cell["indexBox"][2] = cell["indexBox"][2] - index_cut_up
            # 将每个box中subline的坐标也同步更新
            for subline in cell["subLines"]:
                subline["box"][1] = subline["box"][1] - up_line
                subline["box"][3] = subline["box"][3] - up_line
    # 移除remove_list中的cell
    for id in remove_list:
        for cell in image_json["cells"]:
            if cell["id"] == id:
                image_json["cells"].remove(cell)

    # # 将new_image_json保存到json_output_folder
    # name, ext = os.path.splitext(new_image_json["tableImages"][0]["md5"])
    # output_name = f"{name}.json"
    # output_path = os.path.join(json_output_folder, output_name)
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     json.dump(new_image_json, f, ensure_ascii=False, indent=4)

    # 裁剪image，修改json中图片的宽高
    image = image.crop((0, up_line, image.size[0], low_line))
    image_json["tableImages"][0]["width"] = image.size[0]
    image_json["tableImages"][0]["height"] = image.size[1]

    return image


def cut_image(image_json, image, json_output_folder, image_output_folder):
    new_image_json = deepcopy(image_json)
    line = new_image_json["line"]
    # print(line)
    # 定义上下裁切的线段
    up_line, low_line = line, line
    index_cut_up = 0
    # 遍历cells中的box，找到和line相接的cells的最高坐标和最低坐标
    for cell in new_image_json["cells"]:
        if line - 15 < cell["box"][3] < line + 15:  # 如果当前cell的下边界与line相接
            if cell["box"][1] < up_line:  # 如果当前cell的上边界高于up_line
                up_line = cell["box"][1]  # 更新up_line
                index_cut_up = cell["indexBox"][0]  # 更新上部要被切去的索引
        if line - 15 < cell["box"][1] < line + 15:
            if cell["box"][3] > low_line:  # 如果当前cell的下边界低于low_line
                low_line = cell["box"][3]  # 更新low_line
    # 遍历cells中的box，移除up_line之上的box和low_line之下的box，并更新其余box的坐标和indexBox
    new_image_json["line"] -= up_line
    remove_list = []
    for cell in new_image_json["cells"]:
        if cell["box"][3] < up_line + 8:  # 如果当前cell的下边界高于up_line
            remove_list.append(cell["id"])
        elif cell["box"][1] > low_line - 8:  # 如果当前cell的上边界低于low_line
            remove_list.append(cell["id"])
        else:  # 其余要保留的cell
            cell["box"][1] = cell["box"][1] - up_line
            cell["box"][3] = cell["box"][3] - up_line
            cell["indexBox"][0] = cell["indexBox"][0] - index_cut_up
            cell["indexBox"][2] = cell["indexBox"][2] - index_cut_up
            # 将每个box中subline的坐标也同步更新
            for subline in cell["subLines"]:
                subline["box"][1] = subline["box"][1] - up_line
                subline["box"][3] = subline["box"][3] - up_line
    # 移除remove_list中的cell
    for id in remove_list:
        for cell in new_image_json["cells"]:
            if cell["id"] == id:
                new_image_json["cells"].remove(cell)

    # # 将new_image_json保存到json_output_folder
    # name, ext = os.path.splitext(new_image_json["tableImages"][0]["md5"])
    # output_name = f"{name}.json"
    # output_path = os.path.join(json_output_folder, output_name)
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     json.dump(new_image_json, f, ensure_ascii=False, indent=4)

    # 裁剪image，修改json中图片的宽高
    image = image.crop((0, up_line, image.size[0], low_line))
    new_image_json["tableImages"][0]["width"] = image.size[0]
    new_image_json["tableImages"][0]["height"] = image.size[1]
    # 将new_image_json保存到json_output_folder
    name, ext = os.path.splitext(new_image_json["tableImages"][0]["md5"])
    output_name = f"{name}.json"
    output_path = os.path.join(json_output_folder, output_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_image_json, f, ensure_ascii=False, indent=4)
    # 保存image
    image_name = new_image_json['tableImages'][0]['md5']
    image_output_path = os.path.join(image_output_folder, image_name)
    image.save(image_output_path)


def process_uncut_files(json_input_folder, image_input_folder, json_output_folder, image_output_folder):
    # 遍历 JSON 文件夹中的所有 JSON 文件
    for filename in os.listdir(json_input_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_input_folder, filename)
            # 读取 JSON 文件
            # print(json_path)
            with open(json_path, 'r', encoding='utf-8') as f:
                image_json = json.load(f)
                image_name = image_json['tableImages'][0]['md5']
                image_path = os.path.join(image_input_folder, image_name)
                image = Image.open(image_path)
                cut_image(image_json, image, json_output_folder, image_output_folder)


# 测试
if __name__ == '__main__':

    # json_input_folder = './样例/output'
    # image_input_folder = './样例/output'
    # json_output_folder = './样例/output2'
    # image_output_folder = './样例/output2'

    json_input_folder = 'F:/恒生/data/Fund/mix_generate/json'
    image_input_folder = 'F:/恒生/data/Fund/mix_generate/images'
    json_output_folder = 'F:/恒生/data/Fund/mix_cut/json'
    image_output_folder = 'F:/恒生/data/Fund/mix_cut/images'

    process_uncut_files(json_input_folder, image_input_folder, json_output_folder, image_output_folder)
