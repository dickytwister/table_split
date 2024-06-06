import os
import shutil
import json


def copy_matched_json_files(json_folder, source_folder, destination_folder):
    # 遍历C文件夹中的所有图片文件
    for image_filename in os.listdir(destination_folder):
        if image_filename.endswith('.png'):
            image_md5 = os.path.splitext(image_filename)[0] + '.png'
            print(image_md5)
            # 遍历B文件夹中的所有JSON文件
            for json_filename in os.listdir(source_folder):
                if json_filename.endswith('.json'):
                    json_path = os.path.join(source_folder, json_filename)
                    with open(json_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        # 检查JSON文件中的md5字段
                        for i in range(2):
                            for entry in data['tableLabelList'][i]['tableImages']:
                                if entry['md5'] == image_md5:
                                    # 复制JSON文件到A文件夹
                                    destination_file_path = os.path.join(json_folder, json_filename)
                                    shutil.copy(json_path, destination_file_path)
                                    print(f'Copied JSON file {json_filename} from {source_folder} to {json_folder}')
                                    break  # 如果找到匹配的JSON文件，则跳出内部循环


# 指定A文件夹、B文件夹和C文件夹的路径
json_folder = './json_test'
source_folder = 'F:\恒生\original_data\Fund\json'
destination_folder = './imgs_test'

# 执行复制匹配JSON文件的函数
copy_matched_json_files(json_folder, source_folder, destination_folder)
