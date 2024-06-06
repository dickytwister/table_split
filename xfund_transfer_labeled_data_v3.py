import os
import json
import random
from pathlib import Path
from typing import List
from service.base_models import MixImageTextTable


def load_xfund_object(json_dir_path: Path) -> List[MixImageTextTable]:
    documents = []
    json_dir_path = Path(json_dir_path)
    for file in json_dir_path.glob('*.json'):  # 搜索json_dir_path下的所有.json文件
        with file.open(encoding='utf-8') as f:
            data = json.load(f)
        documents.append(MixImageTextTable.parse_obj(data).to_xfund_2(model_name='table_merge'))  # 假设每个文件只包含一个MixImageTextTable对象
    return {"documents": [k.dict() for k in documents]}



def main():
    dataset_path = Path('F:\恒生\data\json')
    train_path = Path('F:\恒生\data/tablemerge.train.json')

    # 读取MixImageTextTable对象
    xfund_json = load_xfund_object(dataset_path)
    # 将xfund_json生成json文件并输出到train_path
    with train_path.open('w', encoding='utf-8') as f:
        json.dump(xfund_json, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
