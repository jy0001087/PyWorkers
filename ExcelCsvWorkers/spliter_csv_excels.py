import pandas as pd
import os
import argparse
import sys

## 用途
# 按第一列分类拆分 CSV / Excel 文件（强力容错版）
# 额外：如果输入目录下存在名为 filter 的文件（filter.xlsx / filter.csv 等），
#       则用其第一列对输入文件的第二列进行过滤，仅保留匹配行。

SUPPORTED_EXT = ('.csv', '.xls', '.xlsx', '.xlsm', '.xlsb', '.xlxs')  # 兼容可能的拼写错误 .xlxs


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


def find_filter_file(directory):
    for f in os.listdir(directory):
        name, ext = os.path.splitext(f)
        if name.lower() == 'filter' and ext.lower() in SUPPORTED_EXT:
            return os.path.join(directory, f)
    raise FileNotFoundError("未在输入目录找到名为 filter 的过滤文件 (filter.xlsx / filter.csv 等)")


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
        description="按第一列分类拆分 CSV / Excel 文件（强力容错版），并可使用同目录下的 filter 文件对第二列进行过滤"
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

    # 校验至少有两列
    if df.shape[1] < 2:
        print("❌ 输入文件列数不足，至少需要两列用于过滤与分组")
        sys.exit(1)

    # 尝试在输入目录查找 filter 文件并进行过滤
    filter_applied = False
    try:
        filter_file = find_filter_file(input_dir)
        print(f"🔎 找到过滤文件: {filter_file}，正在读取并应用过滤...")
        filter_df = read_input_file(filter_file)
        # 标记已执行过滤（即 filter 文件存在并已读取）
        filter_applied = True
    except FileNotFoundError:
        # 未找到 filter 文件时按原逻辑继续
        print("ℹ️ 未找到 filter 文件，跳过过滤步骤")

    if filter_applied:
        if filter_df.shape[1] < 1:
            print("❌ 过滤文件无列可用")
            sys.exit(1)

        # 取过滤文件第一列的值集合（去除空并统一为字符串）
        allowed = set(filter_df.iloc[:, 0].astype(str).str.strip().dropna())

        # 将输入文件第二列也统一为字符串并去除首尾空格
        second_col = df.columns[1]
        df[second_col] = df[second_col].astype(str).str.strip()

        # 只保留在允许集合中的行，并输出被过滤的行数与剩余行数
        before_count = len(df)
        mask = df[second_col].isin(allowed)
        df = df[mask]
        removed = before_count - len(df)

        if df.empty:
            print(f"⚠️ 过滤后无数据，已过滤行数: {removed}，退出。")
            sys.exit(0)

        print(f"✅ 过滤后剩余行数: {len(df)}，已过滤行数: {removed}")

    first_col = df.columns[0]
    grouped = df.groupby(first_col)
    total = len(grouped)

    # 3. 输出目录
    # 使用与输入文件同名的文件夹（去除扩展名）
    # 如果执行了过滤，则在文件夹名后追加 "-过滤后"
    if filter_applied:
        output_root = os.path.join(input_dir, base_name + "-过滤后")
    else:
        output_root = os.path.join(input_dir, base_name)
    os.makedirs(output_root, exist_ok=True)

    print(f"📂 输出目录: {output_root}")
    print(f"📦 分类总数: {total}")

    # 4. 拆分并输出
    for i, (category, group) in enumerate(grouped):
        safe_cat = safe_filename(category)
        # 如果执行了过滤，则在文件名（扩展名前）追加 "-过滤后"
        if filter_applied:
            output_name = f"{base_name}-{safe_cat}-过滤后{ext}"
        else:
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
