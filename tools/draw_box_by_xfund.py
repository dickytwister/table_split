import json
import os
from PIL import Image, ImageDraw


# 打开json文件
with open('F:\恒生\data/tablemerge.train.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
image_source_folder = 'F:\恒生\data/images'
image_output_folder = 'F:\恒生\data/images_draw'
# 遍历data["documents"]中的所有元素
for image in data["documents"]:
    image_name = image["img"]["fname"]
    image_path = image_source_folder + '/' + image_name
    # 打开图片
    # 打开图像
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    for cell in image["document"]:
        draw.rectangle(cell["box"], outline='red')
    output_path = os.path.join(image_output_folder, image_name)
    img.save(output_path)
