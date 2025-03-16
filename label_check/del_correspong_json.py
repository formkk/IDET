import os


def clean_orphan_json_files(directory):
    """
    清理没有对应BMP文件的JSON文件
    :param directory: 要扫描的根目录路径
    """
    deleted_count = 0
    preserved_count = 0

    # 遍历目录树
    for root, _, files in os.walk(directory):
        # 筛选JSON文件
        json_files = [f for f in files if f.lower().endswith('.json')]

        for json_file in json_files:
            # 构造完整路径
            json_path = os.path.join(root, json_file)

            # 生成BMP文件名（支持大小写敏感系统）
            base_name = os.path.splitext(json_file)[0]  # 处理多扩展名情况
            bmp_candidates = [
                base_name + ext for ext in ['.bmp', '.BMP', '.Bmp']
            ]

            # 检查是否存在对应BMP文件
            has_pair = any(
                os.path.exists(os.path.join(root, bmp))
                for bmp in bmp_candidates
            )

            # 执行删除操作
            if not has_pair:
                try:
                    os.remove(json_path)
                    print(f"🗑️ 已删除孤立文件: {json_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 删除失败: {json_path} - {str(e)}")
            else:
                preserved_count += 1
                print(f"✅ 保留有效文件: {json_path}")

    # 输出统计报告
    print(f"\n操作完成！共处理文件：")
    print(f"  → 删除孤立JSON文件: {deleted_count} 个")
    print(f"  → 保留有效文件: {preserved_count} 个")


if __name__ == '__main__':
    # 使用示例 - 修改为你的目录路径
    target_directory = "e:/idet_v2_part1_obv"

    # 安全确认
    confirm = input(f"即将扫描目录：{target_directory}\n确认执行操作？(y/n) ")

    if confirm.lower() == 'y':
        clean_orphan_json_files(target_directory)
    else:
        print("操作已取消")