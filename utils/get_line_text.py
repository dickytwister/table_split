from PIL import Image, ImageDraw
import json
import os


def get_horizontal_lines_text(data, image_folder, pic_num):
    # 获取表格图片的信息
    image_name = data['tableLabelList'][pic_num]['tableImages'][0]['md5']
    image_path = os.path.join(image_folder, image_name)

    # 检查图片文件是否存在，跳过json文件对应不到的图片
    if not os.path.exists(image_path):
        # print(f"Image file '{image_name}' not found in '{image_folder}'. Skipping...")
        return
    # print(image_name)
    lines = []

    # 打开图像
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # 存储每行最大和最小的 y 坐标值
    row_y_coordinates = []

    # 遍历每个单元格中的 subLines，找到每行的最大和最小的 y 坐标值
    for cell in data['tableLabelList'][pic_num]['cells']:
        for subline in cell['subLines']:
            box = subline['box']
            # 获取 y 坐标值
            y_top = round(box[1])
            y_bottom = round(box[3])
            # 将 y 坐标值添加到列表中
            if [y_top, y_bottom] not in row_y_coordinates:
                # 去除重复的y坐标
                if row_y_coordinates and (row_y_coordinates[-1][0] - 2 < y_top < row_y_coordinates[-1][0] + 2 or
                                          row_y_coordinates[-1][1] - 2 < y_bottom < row_y_coordinates[-1][1] + 2):
                    continue
                row_y_coordinates.append([y_top, y_bottom])
                # print(row_y_coordinates)

    # 绘制横线
    pre_line = 0  # 用于记录上一次画线的纵坐标
    for i in range(0, len(row_y_coordinates) - 1):
        y_bottom = row_y_coordinates[i][1]
        y_top = row_y_coordinates[i + 1][0]

        # 添加判断条件，检查 (y_top + y_bottom) / 2 是否在 row_y_coordinates 中的任何一个范围内
        should_draw_line = True
        for y_range in row_y_coordinates:
            if y_range[0] <= (y_top + y_bottom) / 2 <= y_range[1]:
                should_draw_line = False
                break

        for cell in data['tableLabelList'][pic_num]['cells']:
            if cell["box"][3] - 10 < (y_top + y_bottom) / 2 < cell["box"][3] + 10:
                should_draw_line = False
                break

        # 如果不需要画线，则跳过当前循环迭代
        if not should_draw_line or pre_line - 4 < (y_top + y_bottom) / 2 < pre_line + 4:
            continue

        # 否则，画线
        # draw.line([(0, (y_top + y_bottom) / 2), (img.width, (y_top + y_bottom) / 2)], fill='red', width=2)
        # pre_line = (y_top + y_bottom) / 2
        # print(pre_line)

        lines.append((y_top + y_bottom) / 2)

    # 保存绘制后的图像到输出文件夹
    # output_path = os.path.join('D:/PycharmProjects/table_split/样例/output', image_name)
    # img.save(output_path)

    return lines


def process_json_files(json_folder, image_folder, output_folder):
    # 遍历 JSON 文件夹中的所有 JSON 文件
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)
            # 读取 JSON 文件
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # print(f)
                # print(data['tableLabelList'][0]['tableImages'][0]['md5'])
            # 处理 JSON 数据
            for pic_num in range(2):
                lines = get_horizontal_lines_text(data, image_folder, pic_num)
                print(lines)


if __name__ == "__main__":
    json_folder = './样例'
    image_folder = './样例'
    output_folder = './imgs_out'

    process_json_files(json_folder, image_folder, output_folder)
