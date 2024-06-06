import json
from copy import deepcopy


def json_replace(xfund_json):
    # 创建一个新的json对象
    new_data = deepcopy(xfund_json)
    delete_document_id = []
    for i in range(len(new_data["documents"])):  # 遍历每个表格
        all_match = True
        new_data["documents"][i]["document"] = []
        for cell in xfund_json["documents"][i]["document"]:
            if not cell["linking"]:
                continue
            # new_data["documents"][i]["document"].append(cell)
            match = False
            for j in range(len(xfund_json["documents"][i]["document"])):
                if xfund_json["documents"][i]["document"][j]["id"] == cell["linking"][0][1]:
                    match = True
                    new_data["documents"][i]["document"].append(cell)
                    new_data["documents"][i]["document"].append(xfund_json["documents"][i]["document"][j])
            if not match:
                all_match = False
            if cell["box"][0] > cell["box"][2] or cell["box"][1] > cell["box"][3]:  # 去除错误框
                all_match = False
        if not all_match:
            # 记录要移除的图片
            delete_document_id.append(i)
    # 遍历new_data["documents"], 删除不符合要求的图片
    for i in range(len(delete_document_id)):
        new_data["documents"].pop(delete_document_id[i] - i)

    return new_data


if __name__ == '__main__':
    with open('D:/Desktop/xfund/train/train_0.json', 'r', encoding='utf-8') as f:
        xfund_json = json.load(f)
    new_data = json_replace(xfund_json)
    with open('D:/Desktop/xfund/train/train_0_new.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
