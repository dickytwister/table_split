import os
import shutil
import json


def copy_files(json_folder, source_folder, destination_folder):
    # 遍历A文件夹中的所有JSON文件
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)
            with open(json_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                # 检查JSON文件中的md5字段，并从B文件夹中找到对应的文件，移动到C文件夹
                for entry in data['tableLabelList'][1]['tableImages']:
                    md5 = entry['md5']
                    source_file_path = os.path.join(source_folder, md5)
                    destination_file_path = os.path.join(destination_folder, md5)
                    if os.path.exists(source_file_path):
                        shutil.copy(str(source_file_path), str(destination_file_path))
                        print(f'Copied file {md5} from {source_folder} to {destination_folder}')
                    else:
                        print(f'File {md5} not found in {source_folder}')

# 指定A文件夹、B文件夹和C文件夹的路径
json_folder = 'C:/Users/baoyc53387/Desktop/table_split/json'
source_folder = 'D:/PycharmProjects/table_split/imgs'
destination_folder = 'C:/Users/baoyc53387/Desktop/table_split/images'

# 执行移动文件的函数
copy_files(json_folder, source_folder, destination_folder)
