import os
import json
from collections import defaultdict

# 合法的label范围
VALID_LABELS = set(range(1, 38))  # 1到37的整数

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
    "20": "分层(PP分层/纸张分层)",
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


def extract_filename(file_name):
    """提取文件名中第3个'_'之后、第1个'.'之前的部分"""
    parts = file_name.split('_')
    if len(parts) > 3:
        # 取第3个'_'之后的部分
        after_third_underscore = '_'.join(parts[3:])
        # 取第1个'.'之前的部分
        before_first_dot = after_third_underscore.split('.')[0]
        return before_first_dot
    return file_name  # 如果不足3个'_'，返回原文件名


def count_labels_in_json(file_path):
    """统计单个JSON文件中的label数量"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    labels = set()
    for shape in data.get('shapes', []):
        label = shape.get('label')
        if label is not None:
            try:
                label = int(label)  # 尝试将label转换为整数
                if label in VALID_LABELS:
                    labels.add(label)
            except (ValueError, TypeError):
                # 如果label不是整数，跳过
                continue
    return labels


def count_labels_in_directory(directory):
    """统计指定目录下所有JSON文件中的label数量，并记录文件名"""
    label_file_count = defaultdict(int)  # 统计每个label的数量
    label_file_names = defaultdict(list)  # 记录每个label出现的文件名

    # 遍历目录下的所有文件
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                labels = count_labels_in_json(file_path)

                # 提取文件名中第3个'_'之后、第1个'.'之前的部分
                extracted_name = extract_filename(file_name)

                # 更新统计结果
                for label in labels:
                    label_file_count[label] += 1
                    label_file_names[label].append(extracted_name)

    return label_file_count, label_file_names


def save_results_to_txt(label_file_count, label_file_names, output_file):
    """将统计结果保存到txt文件，包括总结和详细信息"""
    with open(output_file, 'w', encoding='utf-8') as f:
        if label_file_count:
            # 总结部分：列出所有label及其总出现次数
            f.write("总结：各个label的总出现次数\n")
            f.write("==========================\n")
            for label in sorted(label_file_count.keys()):
                description = LABEL_DESCRIPTION.get(str(label), "未知")
                f.write(f"Label '{label}' ({description}): {label_file_count[label]} 次\n")
            f.write("\n\n")

            # 详细信息部分：按数量升序排列，列出每个label的文件名
            f.write("详细信息：各个label的统计结果（按数量升序排列）\n")
            f.write("=============================================\n")
            sorted_labels = sorted(label_file_count.items(), key=lambda x: x[1])
            for label, count in sorted_labels:
                description = LABEL_DESCRIPTION.get(str(label), "未知")
                f.write(f"Label '{label}' ({description}): {count} 次\n")
                f.write(f"出现该label的文件名: {', '.join(label_file_names[label])}\n")
                f.write("\n")
        else:
            f.write("未找到任何JSON文件或合法的label数据。\n")


def main():
    # 指定目录路径
    directory = input("请输入要统计的目录路径: ").strip()

    if not os.path.isdir(directory):
        print("指定的路径不是目录！")
        return

    # 统计label数量及文件名
    label_file_count, label_file_names = count_labels_in_directory(directory)

    # 输出结果到txt文件
    output_file = "label_statistics_result.txt"
    save_results_to_txt(label_file_count, label_file_names, output_file)
    print(f"统计结果已保存到文件: {output_file}")


if __name__ == "__main__":
    main()