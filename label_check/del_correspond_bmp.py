import os
import sys


def find_json_basenames(directory):
    """构建所有JSON文件的文件名索引（不包含扩展名）"""
    json_basenames = set()

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.json'):
                # 提取基础文件名（支持多扩展名情况，如 image.001.json → image.001）
                base = os.path.splitext(filename)[0]
                if base.endswith('.json'):
                    base = base[:-5]  # 处理双扩展名异常情况
                json_basenames.add(base.lower())  # 统一小写处理
    return json_basenames


def clean_orphan_bmp(directory, json_basenames):
    """清理没有JSON配对的BMP文件"""
    deleted = 0
    preserved = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(('.bmp', '.dib')):  # 支持BMP格式的常见扩展名
                bmp_path = os.path.join(root, filename)

                # 提取基础文件名（兼容大小写）
                base = os.path.splitext(filename)[0].lower()

                # 检查是否存在对应JSON
                if base not in json_basenames:
                    try:
                        os.remove(bmp_path)
                        print(f"🗑️ 已删除孤立文件: {bmp_path}")
                        deleted += 1
                    except Exception as e:
                        print(f"❌ 删除失败 [{e}]: {bmp_path}")
                else:
                    preserved += 1
                    print(f"✅ 保留有效文件: {bmp_path}")

    return deleted, preserved


def main(target_dir):
    """主控制流程"""
    print("🕵️ 正在扫描JSON文件...")
    json_index = find_json_basenames(target_dir)

    print("\n🔍 开始检查BMP文件...")
    del_count, keep_count = clean_orphan_bmp(target_dir, json_index)

    print("\n📊 清理报告:")
    print(f"删除孤立BMP文件: {del_count} 个")
    print(f"保留有效BMP文件: {keep_count} 个")


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("用法: python clean_orphan_bmp.py <目标目录>")
    #     sys.exit(1)

    # target = sys.argv[1]
    target = "e:/idet_v2_part1_obv"

    if not os.path.isdir(target):
        print(f"错误: 目录不存在 - {target}")
        sys.exit(1)

    # 安全确认
    confirm = input(f"即将扫描目录: {target}\n确认执行清理操作？(y/N) ").strip().lower()

    if confirm == 'y':
        main(target)
        print("✅ 操作完成")
    else:
        print("🚫 操作已取消")