import pandas as pd
import os
import argparse
import sys

## 用途
# 按第一列分类拆分 CSV / Excel 文件（强力容错版）

SUPPORTED_EXT = ('.csv', '.xls', '.xlsx', '.xlsm', '.xlsb')


def find_single_input_file(directory):
    files = [
        f for f in os.listdir(directory)
        if f.lower().endswith(SUPPORTED_EXT)
    ]
    if len(files) == 0:
        raise FileNotFoundError("当前目录下未找到任何支持的输入文件")
    if len(files) > 1:
        raise RuntimeError(f"当前目录下发现多个输入文件，请使用 -i 指定：{files}")
    return os.path.join(directory, files[0])


def read_input_file(input_file):
    ext = os.path.splitext(input_file)[1].lower()

    if ext == '.csv':
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            df = pd.read_csv(f)
    else:
        df = pd.read_excel(input_file)

    if df.empty:
        raise ValueError("输入文件为空")

    return df


def safe_filename(name):
    return str(name).strip().replace('/', '_').replace('\\', '_')


def main():
    parser = argparse.ArgumentParser(
        description="按第一列分类拆分 CSV / Excel 文件（强力容错版）"
    )
    parser.add_argument(
        "-i", "--input",
        help="输入文件路径（csv / excel），不指定则使用当前目录下的单一文件"
    )

    args = parser.parse_args()

    # 1. 确定输入文件
    if args.input:
        input_file = os.path.abspath(args.input)
        if not os.path.isfile(input_file):
            print(f"❌ 输入文件不存在: {input_file}")
            sys.exit(1)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_file = find_single_input_file(script_dir)

    print(f"📥 输入文件: {input_file}")

    input_dir = os.path.dirname(input_file)
    base_name, ext = os.path.splitext(os.path.basename(input_file))

    # 2. 读取数据
    print("📊 正在读取数据（强力容错模式）...")
    df = read_input_file(input_file)

    first_col = df.columns[0]
    grouped = df.groupby(first_col)
    total = len(grouped)

    # 3. 输出目录
    output_root = os.path.join(input_dir, "output")
    os.makedirs(output_root, exist_ok=True)

    print(f"📂 输出目录: {output_root}")
    print(f"📦 分类总数: {total}")

    # 4. 拆分并输出
    for i, (category, group) in enumerate(grouped):
        safe_cat = safe_filename(category)
        output_name = f"{base_name}-{safe_cat}{ext}"
        output_path = os.path.join(output_root, output_name)

        if ext == '.csv':
            group.to_csv(output_path, index=False, encoding='utf-8-sig')
        else:
            group.to_excel(output_path, index=False)

        if (i + 1) % 20 == 0 or (i + 1) == total:
            print(f"进度: {i + 1}/{total}")

    print("\n✅ 处理完成")


if __name__ == "__main__":
    main()
