## 主入口  
### [process.sh](process.sh)   

## 核心代码  
### [table_split.py](table_split.py) 

## 相关工具
### 数据增强主流程
  + [mix_generate3.py](utils/mix_generate3.py) 生成mix格式文件，包括去掉首尾的画线
  + [mix_cut.py](utils/mix_cut.py) 根据所画的线对图片和json文件进行裁剪并输出
  + [add_relations_lableid.py](utils/add_relations_labelid.py) 对生成的json文件补充没有合并关系单元格的标注
  + [xfund_transfer_labeled_data_v3.py](xfund_transfer_labeled_data_v3.py) 根据json文件生成xfund标注格式文件
  + [json_repalce.py](utils/json_replace.py) 将xfund标注文件中相互关联的单元格放在一起，无法匹配的document从文件中删除

### 删除训练时出现empty的数据
  + 将id+empty拷贝到txt文件
  + [reshape_delete.py](tools/reshape_delete.py) 将txt文件整理成只有id
  + [delete_empty2.py](tools/delete_empty2.py) delete_empty2.py 从xfund文件中删除带有id的图片标注

### 画框工具
  + [draw_box_2.py](tools/draw_box_2.py) 根据上游提供的包含两张表格的json文件画单元格框
  + [draw_cellbox_mix.py](tools/draw_cellbox_mix.py) 根据生成的mix格式文件画单元格框
  + [draw_sublinebox_mix.py](tools/draw_sublinebox_mix.py) 根据生成的mix格式文件画subline框
  + [draw_box_by_xfund.py](tools/draw_box_by_xfund.py) 根据xfund文件画sublines合并框

### 画线工具
  + [draw_line_box.py](tools/draw_line_box.py) 根据上游的json文件在图片上根据单元格边缘划线
  + [draw_line_text.py](tools/draw_line_text.py) 根据上游的json文件在图片上根据sublinebox的边界划线

### 图片与json互相获取
  + [get_pic_2.py](tools/get_pic_2.py) 根据文件夹中的json获取对应图片
  + [get_json_2.py](tools/get_json_2.py) 根据文件夹中的图片获取对应json
  + [delete_json_not_in_image.py](tools/delete_json_not_in_image.py) 将xfund标注文件中不存在与image文件夹下的标注删除

### 数据划分
  + [data_split.py](tools/data_split.py) 将数据划分成带merged标签和不带merged标签两类
  + [get_val.py](tools/get_val.py) 将json文件夹下的mix格式文件划分出验证集
  + [get_val_by_xfund.py](tools/get_val_by_xfund.py) 将mix生成的xfund标注文件划分出验证集

