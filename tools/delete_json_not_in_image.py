import json
import os
from copy import deepcopy

with open('tablemerge.train3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
image_folder = 'F:/恒生/data/xfund-tablemerge/images_draw'
image_files = set(os.listdir(image_folder))
# print(data)
# 创建一个新的json对象
new_data = deepcopy(data)
delete_document_id = []

for i in range(len(new_data["documents"])):
    # 如果new_data["documents"][i]["img"]["fname"]不在image_folder中
    if new_data["documents"][i]["img"]["fname"] not in image_files:
        delete_document_id.append(i)
print(delete_document_id)
# 遍历new_data["documents"]，删除delete_document_id对应图片
for i in range(len(delete_document_id)):
    new_data["documents"].pop(delete_document_id[i] - i)
# 保存到新的json文件
with open('F:/恒生/data/xfund-tablemerge/tablemerge.train4.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=4)
