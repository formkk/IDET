import os
import json
import sys
from collections import defaultdict

# 参考表：label编号与中文说明的映射
LABEL_DESCRIPTION = {
    "1": "色差",
    "2": "套印不准",
    "3": "字体残缺",
    "4": "点缺陷",
    "5": "擦花",
    "6": "亮印",
    "7": "墨杠",
    "8": "水杠",
    "9": "深度划痕",
    "10": "轻微划痕",
    "11": "爆刀爆线",
    "12": "爆色/脱漆",
    "13": "锯齿",
    "14": "易脆",
    "15": "超线/离线",
    "16": "除泡不实/气泡",
    "17": "凹凸点或凹凸包",
    "18": "折皱",
    "19": "PP边线泛白",
    "20": "分层 PP分层/纸张分层",
    "21": "PP膜破损、覆膜不全",
    "22": "折痕/压痕",
    "23": "脏污",
    "24": "粘贴开胶",
    "25": "面纸脱胶",
    "26": "溢胶",
    "27": "残胶/胶水痕",
    "28": "烫印掉粉",
    "29": "偏位",
    "30": "皱角/爆角",
    "31": "刀位同坑纸",
    "32": "成品掉粉",
    "33": "毛丝",
    "34": "除废不良",
    "35": "破损",
    "36": "V槽破损",
    "37": "灰板漏灰",
}


def get_labels_in_json(file_path):
    """获取单个JSON文件中的所有label"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 使用集合去重，确保每个label在单个文件中只统计一次
    labels = set()
    for shape in data.get('shapes', []):
        label = shape.get('label')
        if label is not None:
            labels.add(label)
    return labels


def count_labels_in_directory(directory):
    """统计指定目录下所有JSON文件中每个label出现的文件数量"""
    label_file_count = defaultdict(int)

    # 遍历目录下的所有文件
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                labels = get_labels_in_json(file_path)

                # 统计每个label出现的文件数量
                for label in labels:
                    label_file_count[label] += 1

    return label_file_count


def save_results_to_txt(label_file_count, output_file):
    """将统计结果保存到txt文件，并按数量升序排列，同时加入中文说明"""
    with open(output_file, 'w', encoding='utf-8') as f:
        if label_file_count:
            f.write("各个label在JSON文件中出现的次数（按数量升序排列）：\n")
            # 按数量升序排列
            sorted_labels = sorted(label_file_count.items(), key=lambda x: x[1])
            for label, count in sorted_labels:
                # 获取中文说明，如果label不在参考表中，则显示“未知”
                description = LABEL_DESCRIPTION.get(label, "未知")
                f.write(f"Label '{label}' ({description}): {count} 个文件\n")
        else:
            f.write("未找到任何JSON文件或label数据。\n")


def main():
    # 指定目录路径
    # directory = input("请输入要统计的目录路径: ").strip()
    directory = "e://idet_data/json"

    if not os.path.isdir(directory):
        print("指定的路径不是目录！")
        return

    # 统计每个label在JSON文件中出现的次数
    label_file_count = count_labels_in_directory(directory)

    # 输出结果到txt文件
    output_file = "label_statistics.txt"
    save_results_to_txt(label_file_count, output_file)
    print(f"统计结果已保存到文件: {output_file}")


if __name__ == "__main__":
    main()