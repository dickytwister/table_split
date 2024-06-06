import random
import json
from copy import deepcopy

# 打开json文件
with open('F:/恒生/data/tablemerge.train2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nums = []
while len(nums) < len(data["documents"]) * 0.1:  # 分出20%是*0.1
    num = random.randint(0, len(data["documents"]) - 1)
    if num % 2 == 0 and num not in nums:
        nums.append(num)

nums.sort()
# print(nums)

train_data = deepcopy(data)
val_data = deepcopy(data)
# print(len(train_data["documents"]))

val_data["documents"] = []
for i in range(len(nums)):
    val_data["documents"].append(train_data["documents"][nums[i] - 2 * i])
    val_data["documents"].append(train_data["documents"][nums[i] - 2 * i + 1])
    train_data["documents"].pop(nums[i] - 2 * i)
    train_data["documents"].pop(nums[i] - 2 * i + 1)

# 保存到新的json文件
with open('F:/恒生/data/增强数据拆分的训练集与验证集/tablemerge.train.json', 'w', encoding='utf-8') as f:
    json.dump(train_data, f, ensure_ascii=False, indent=4)
with open('F:/恒生/data/增强数据拆分的训练集与验证集/tablemerge.val.json', 'w', encoding='utf-8') as f:
    json.dump(val_data, f, ensure_ascii=False, indent=4)
