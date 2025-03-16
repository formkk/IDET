import os
import json

def process_json_file(json_path):
    """处理单个 JSON 文件"""
    try:
        # 读取 JSON 文件内容
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 文件读取失败 | {json_path} | 错误: {str(e)}")
        return

    # 检查关键数据结构是否存在
    if 'shapes' not in data:
        print(f"🗑️ 删除文件（缺少shapes键）| {json_path}")
        os.remove(json_path)
        return

    # 过滤符合条件的标注
    valid_shapes = []
    for shape in data['shapes']:
        # 检查标注是否包含坐标点
        if 'points' not in shape or len(shape['points']) != 2:
            continue  # 跳过无效标注

        try:
            # 解析坐标点（支持整数/浮点数字符串）
            [[x1, y1], [x2, y2]] = [
                [float(coord) for coord in point]
                for point in shape['points']
            ]
        except (ValueError, TypeError):
            continue  # 跳过坐标格式错误的标注

        # 计算最大边长
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        max_side = max(dx, dy)

        # 保留边长 > 16 的标注
        if max_side > 16:
            valid_shapes.append(shape)

    # 更新标注数据
    data['shapes'] = valid_shapes

    # 根据标注是否为空决定操作
    if not valid_shapes:
        print(f"🗑️ 删除文件（无有效标注）| {json_path}")
        os.remove(json_path)
    else:
        # 保存修改后的文件（保留原始缩进格式）
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ 文件更新完成 | {json_path}")

def batch_process(directory):
    """批量处理目录"""
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.json'):
                process_json_file(os.path.join(root, filename))

if __name__ == '__main__':
    # 使用方法：修改为你的目录路径
    target_dir = "E:\idet_v2_part1_1500"
    batch_process(target_dir)
    print("处理完成！")