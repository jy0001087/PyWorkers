#!/usr/bin/env python3

# 用途：对大型 CSV 文件进行预检，检查物理完整性、编码、分隔符及结构问题。

import sys
import csv
from pathlib import Path
from collections import Counter

# -----------------------------
# 物理文件完整性检查
# -----------------------------
def check_physical_integrity(path: Path, tail_check_size=4096):
    data = path.read_bytes()
    size = len(data)

    report = {
        "has_null": False,
        "null_only_at_tail": False,
        "null_count": 0,
        "tail_is_all_null": False,
        "ends_with_newline": False,
        "binary_ratio": 0.0,
        "fatal": False,
        "messages": [],
    }

    if b"\x00" in data:
        report["has_null"] = True
        report["null_count"] = data.count(b"\x00")

        stripped = data.rstrip(b"\x00")
        if b"\x00" not in stripped:
            report["null_only_at_tail"] = True
            report["messages"].append(
                "检测到 NULL 字节，仅存在于文件尾部（典型未写完文件）"
            )
        else:
            report["fatal"] = True
            report["messages"].append(
                "检测到 NULL 字节分布在文件中间（严重物理损坏）"
            )

        tail = data[-tail_check_size:]
        if tail and all(b == 0 for b in tail):
            report["tail_is_all_null"] = True

    # 是否以换行结尾
    report["ends_with_newline"] = data.endswith(b"\n")

# -------- 修正后的“非文本 / 二进制”判断 --------

# 1. NULL 字节已经单独处理，这里不再重复

# 2. 统计“控制字符”（不包括 \t \n \r）
    control_bytes = sum(
        1 for b in data
        if b < 32 and b not in (9, 10, 13)
    )

    report["binary_ratio"] = control_bytes / size if size else 0

    # 3. 阈值：控制字符超过 1% 才认为异常
    if report["binary_ratio"] > 0.01:
        report["messages"].append(
            f"检测到异常控制字符比例 {report['binary_ratio']:.2%}，疑似二进制或损坏文件"
        )


    return report


# -----------------------------
# 编码检测
# -----------------------------
def detect_encoding(path: Path, sample_size=100_000):
    import chardet

    raw = path.read_bytes()[:sample_size]
    result = chardet.detect(raw)

    encoding = result["encoding"]
    confidence = result["confidence"]
    bom = raw.startswith(b"\xef\xbb\xbf")

    if bom:
        encoding = "utf-8-sig"

    return encoding, confidence, bom


# -----------------------------
# CSV 结构分析
# -----------------------------
def analyze_structure(path: Path, encoding: str, delimiter: str):
    csv.field_size_limit(sys.maxsize)

    field_counts = Counter()
    empty_lines = 0
    bad_rows = []

    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            lineno = reader.line_num
            if not row or all(not c.strip() for c in row):
                empty_lines += 1
                continue
            field_counts[len(row)] += 1

    expected = field_counts.most_common(1)[0][0]

    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            lineno = reader.line_num
            if row and len(row) != expected:
                bad_rows.append((lineno, len(row)))

    return field_counts, empty_lines, bad_rows


# -----------------------------
# 主流程
# -----------------------------
def main():
    if len(sys.argv) != 2:
        print("用法: python csv_preflight.py <file.csv>")
        sys.exit(1)

    path = Path(sys.argv[1])
    print(f"\n📄 CSV 文件预检报告：{path.name}")
    print("=" * 60)

    # ① 物理完整性
    phys = check_physical_integrity(path)
    print("🧬 物理文件检查:")
    print(f"   - NULL 字节: {'存在' if phys['has_null'] else '未发现'}")
    if phys["has_null"]:
        print(f"   - NULL 数量: {phys['null_count']}")
        print(f"   - 仅尾部 NULL: {phys['null_only_at_tail']}")
        print(f"   - 尾部全 NULL: {phys['tail_is_all_null']}")
    print(f"   - 以换行结尾: {phys['ends_with_newline']}")
    print(f"   - 非文本比例: {phys['binary_ratio']:.2%}")

    for msg in phys["messages"]:
        print(f"   ⚠️ {msg}")

    if phys["fatal"]:
        print("\n❌ 文件存在严重物理损坏，不建议继续解析")
        return

    # ② 编码
    encoding, conf, bom = detect_encoding(path)
    print("\n🔤 编码检测:")
    print(f"   - 编码: {encoding}")
    print(f"   - 置信度: {conf:.2f}")
    print(f"   - BOM: {'是' if bom else '否'}")

    # ③ 分隔符
    import csv as _csv
    sample = path.read_text(encoding=encoding, errors="replace")[:5000]
    delimiter = _csv.Sniffer().sniff(sample).delimiter
    print("\n🔣 分隔符检测:")
    print(f"   - 推测分隔符: '{delimiter}'")

    # ④ CSV 结构
    fields, empty, bad = analyze_structure(path, encoding, delimiter)
    print("\n📊 行与字段结构:")
    for k, v in fields.items():
        print(f"   - {k} 列: {v} 行")
    print(f"   - 空行: {empty}")

    if bad:
        print("\n❌ 字段数异常行:")
        for lineno, cols in bad[:5]:
            print(f"   - 行 {lineno}: {cols} 列")
        if len(bad) > 5:
            print(f"   - 另有 {len(bad)-5} 行未显示")

    print("\n✅ 预检完成\n")


if __name__ == "__main__":
    main()
