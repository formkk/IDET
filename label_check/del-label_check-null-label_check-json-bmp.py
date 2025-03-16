import os
import json

def process_json_file(json_path):
    # 检查是否存在同名 BMP 文件（提前终止条件）
    bmp_path = os.path.splitext(json_path)[0] + ".bmp"
    if not os.path.exists(bmp_path):
        print(f"Deleting {json_path} (no corresponding BMP)")
        os.remove(json_path)
        return

    # 读取 JSON 文件
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {json_path} (invalid JSON: {e})")
        return

    # 检查是否包含必要结构
    if "shapes" not in data:
        print(f"Deleting {json_path} (missing 'shapes' key)")
        os.remove(json_path)
        return

    # 删除 label=33 的条目，并检查 label 键完整性
    valid_shapes = []
    has_invalid_shape = False

    for shape in data["shapes"]:
        if "label" not in shape:
            has_invalid_shape = True  # 标记存在无 label 的条目
        elif shape["label"] == "33":
            continue  # 跳过 label=33 的条目
        else:
            valid_shapes.append(shape)

    # 如果存在无效条目或处理后无有效条目，则删除文件
    if has_invalid_shape or len(valid_shapes) == 0:
        print(f"Deleting {json_path} (invalid/empty shapes)")
        os.remove(json_path)
        return

    # 保存修改后的内容
    data["shapes"] = valid_shapes
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Updated {json_path}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".json"):
                json_path = os.path.join(root, file)
                process_json_file(json_path)

# 使用示例
if __name__ == "__main__":
    target_dir = "e:/idet_v2_part1_1500"
    process_directory(target_dir)
    print("Processing completed!")