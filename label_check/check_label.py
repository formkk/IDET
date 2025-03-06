import os
import json

# 合法的label范围
VALID_LABELS = set(range(1, 38))  # 1到37的整数


def check_labels_in_json(file_path):
    """检查单个JSON文件中的label是否合法"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    invalid_labels = set()
    for shape in data.get('shapes', []):
        label = shape.get('label')
        if label is not None:
            try:
                label = int(label)  # 尝试将label转换为整数
                if label not in VALID_LABELS:
                    invalid_labels.add(label)
            except (ValueError, TypeError):
                # 如果label不是整数，直接视为非法
                invalid_labels.add(label)

    return invalid_labels


def check_labels_in_directory(directory):
    """检查指定目录下所有JSON文件中的label是否合法"""
    invalid_files = {}  # 存储非法label的文件及其对应的非法label

    # 遍历目录下的所有文件
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                invalid_labels = check_labels_in_json(file_path)

                # 如果文件中有非法label，记录下来
                if invalid_labels:
                    invalid_files[file_name] = invalid_labels

    return invalid_files


def save_results_to_txt(invalid_files, output_file):
    """将包含非法label的文件名及其非法label保存到txt文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        if invalid_files:
            f.write("以下文件包含非法的label（非1至37的整数）：\n")
            for file_name, invalid_labels in invalid_files.items():
                f.write(f"文件名: {file_name}\n")
                f.write(f"非法label: {', '.join(map(str, invalid_labels))}\n")
                f.write("\n")
        else:
            f.write("所有文件的label均合法（1至37的整数）。\n")


def main():
    # 指定目录路径
    # directory = input("请输入要检查的目录路径: ").strip()
    directory = "D:\labeled_data\data_labeled_黄底无字"

    if not os.path.isdir(directory):
        print("指定的路径不是目录！")
        return

    # 检查label是否合法
    invalid_files = check_labels_in_directory(directory)

    # 输出结果到txt文件
    output_file = "invalid_label_files.txt"
    save_results_to_txt(invalid_files, output_file)
    print(f"检查结果已保存到文件: {output_file}")


if __name__ == "__main__":
    main()