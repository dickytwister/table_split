from PIL import Image, ImageDraw
import json
import os


def draw_boxes_on_image(data, image_folder, output_folder, pic_num):
    # 获取表格图片的信息
    image_name = data['tableLabelList'][pic_num]['tableImages'][0]['md5']
    image_path = os.path.join(image_folder, image_name)

    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        print(f"Image file '{image_name}' not found in '{image_folder}'. Skipping...")
        return

    # 打开图像
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # 遍历每个单元格中的subLines，并绘制框
    for cell in data['tableLabelList'][pic_num]['cells']:
        for subline in cell['subLines']:
            box = subline['box']

            # 直接绘制框
            draw.rectangle(box, outline='red')

    # 保存绘制后的图像到输出文件夹
    output_path = os.path.join(output_folder, image_name)
    img.save(output_path)


def process_json_files(json_folder, image_folder, output_folder):
    # 遍历JSON文件夹中的所有JSON文件
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            # print(filename)
            json_path = os.path.join(json_folder, filename)
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 处理JSON数据
            for pic_num in range(2):
                draw_boxes_on_image(data, image_folder, output_folder, pic_num)


if __name__ == "__main__":
    json_folder = './json_test'
    image_folder = './imgs_test'
    output_folder = './imgs_out_test'
    # json_folder = './json'
    # image_folder = './imgs'
    # output_folder = './imgs_out'

    process_json_files(json_folder, image_folder, output_folder)
