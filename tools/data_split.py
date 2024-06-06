import os
import json
import shutil


def split_data(json_folder, image_folder, json_merged_output_folder, image_merged_output_folder, json_umerged_output_folder, image_unmerged_output_folder):
    for root, dirs, files in os.walk(json_folder):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    image_json = json.load(f)
                    merged_tag = False
                    for relation in image_json['relations']:
                        if relation['labelId'] == 1:
                            merged_tag = True
                    if merged_tag:
                        # 将当前的json文件复制到json_merged_output_folder，image_json["md5"]对应的image_folder中的图片复制到image_merged_output_folder
                        shutil.copy(str(file_path), str(json_merged_output_folder))
                        shutil.copy(str(os.path.join(image_folder, image_json["tableImages"][0]["md5"])), str(image_merged_output_folder))
                    else:
                        # 将当前的json文件复制到json_umerged_output_folder，image_json["md5"]对应的image_folder中的图片复制到image_unmerged_output_folder
                        shutil.copy(str(file_path), str(json_umerged_output_folder))
                        shutil.copy(str(os.path.join(image_folder, image_json["tableImages"][0]["md5"])), str(image_unmerged_output_folder))


if __name__ == '__main__':

    json_folder = 'E:/恒生/Fund/mix_add_relations/json'
    image_folder = 'E:/恒生/Fund/mix_cut/images'
    json_merged_output_folder = 'E:/恒生/Fund/mix_split_data/merged/json'
    image_merged_output_folder = 'E:/恒生/Fund/mix_split_data/merged/images'
    json_umerged_output_folder = 'E:/恒生/Fund/mix_split_data/unmerged/json'
    image_unmerged_output_folder = 'E:/恒生/Fund/mix_split_data/unmerged/images'

    split_data(json_folder, image_folder, json_merged_output_folder, image_merged_output_folder, json_umerged_output_folder, image_unmerged_output_folder)
