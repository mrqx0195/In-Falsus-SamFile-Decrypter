import os
import sys
import re
import shutil
import argparse
from typing import Dict

def parse_mapping(mappings: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    pattern = re.compile(r'Guid: (\w+) FullLookupPath: (.+)$')
    with open(mappings, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            match = pattern.search(line)
            if match:
                guid = match.group(1)
                path = match.group(2).strip()
                if guid in mapping:
                    print(f"Warning: 第 {line_num} 行 GUID {guid} 重复，覆盖先前映射")
                mapping[guid] = path
    return mapping

def main():
    parser = argparse.ArgumentParser(description="资源重命名工具")
    parser.add_argument("input_dir", help="输入目录")
    parser.add_argument("--mappings", help="映射文件", default="mappings.txt")
    args = parser.parse_args()
    
    decoded_dir = args.input_dir
    mappings = args.mappings

    if not os.path.isdir(decoded_dir):
        raise ValueError(f"目录 '{decoded_dir}' 不存在")
        sys.exit(1)

    if not os.path.isfile(mappings):
        raise ValueError(f"映射文件 '{mappings}' 不存在")
        sys.exit(1)

    mapping = parse_mapping(mappings)
    print(f"加载映射条目: {len(mapping)}")

    success = 0
    failed = 0
    skipped = 0

    for guid, full_path in mapping.items():
        src = os.path.join(decoded_dir, guid)
        if not os.path.exists(src):
            print(f"Warning: 源文件不存在 {src}")
            skipped += 1
            continue
        full_path = full_path.replace('\\', '/')
        dirname, filename = os.path.split(full_path)
        dest_dir = os.path.join(decoded_dir, dirname) if dirname else decoded_dir
        dest = os.path.join(dest_dir, filename)

        try:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src, dest)
            print(f"成功: {guid} -> {dest}")
            success += 1
        except Exception as e:
            print(f"失败: {guid} -> {dest} - {e}")
            failed += 1

    print(f"\n处理完成: 成功 {success} | 失败 {failed} | 跳过 {skipped}")

if __name__ == "__main__":
    main()