import json
from copy import deepcopy

with open('F:/恒生/data/增强数据训练集（全部）/tablemerge.train.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('C:/Users/baoyc53387/Desktop/delete.txt', 'r') as d:
    delete_ids = set(line.strip() for line in d)

new_data = deepcopy(data)
delete_idx = []
for i in range(len(new_data["documents"])):
    if new_data["documents"][i]["id"] in delete_ids:
        delete_idx.append(i)

for i in range(len(delete_idx)):
    new_data["documents"].pop(delete_idx[i] - i)

# 保存到新的json文件
with open('F:/恒生/data/增强数据训练集（全部）/tablemerge.train2.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=4)
