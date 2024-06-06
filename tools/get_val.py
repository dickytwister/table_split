import os
import random
import shutil

# 定义文件夹路径
folder_A = 'D:/Data/split_data/训练集清洗/json'
folder_B = 'D:/Data/split_data/small_amount/json'

# 获取文件夹A中的所有JSON文件
all_files = [f for f in os.listdir(folder_A) if f.endswith('.json')]

# 计算需要剪切的文件数量（20%）
num_files_to_move = int(len(all_files) * 0.1)

# 随机选择需要剪切的文件
files_to_move = random.sample(all_files, num_files_to_move)

# 剪切文件到文件夹B
for file_name in files_to_move:
    src_path = os.path.join(folder_A, file_name)
    dest_path = os.path.join(folder_B, file_name)
    shutil.move(src_path, dest_path)

print(f"Successfully moved {num_files_to_move} files from {folder_A} to {folder_B}")
