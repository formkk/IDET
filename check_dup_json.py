import os


def delete_json_if_bmp_missing(directory):
    # 遍历目录下的所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 检查文件是否为JSON文件
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                # 获取同名的BMP文件路径
                bmp_path = os.path.splitext(json_path)[0] + '.bmp'

                # 如果BMP文件不存在，则删除JSON文件
                if not os.path.exists(bmp_path):
                    print(f"Deleting {json_path} because corresponding BMP file does not exist.")
                    os.remove(json_path)


# 指定要处理的目录
directory = '/home/ca/idet_v2_part1_1460'
delete_json_if_bmp_missing(directory)