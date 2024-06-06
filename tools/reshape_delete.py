def clean_file(file_path):
    # 打开文件并读取所有行
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 处理每一行
    cleaned_lines = []
    for line in lines:
        # 删除"empty"字符串
        line = line.replace("empty", "")
        # 删除行两端的空格
        line = line.strip()
        # 添加处理后的行到列表中
        cleaned_lines.append(line)

    # 将处理后的内容写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in cleaned_lines:
            file.write(line + '\n')


# 使用示例
file_path = 'C:/Users/baoyc53387/Desktop/delete.txt'
clean_file(file_path)
