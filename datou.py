import pandas as pd
import os

input_file = '/Users/rfs/Downloads/datou/2户主手机号码重复统计明细表.csv'
output_dir = '/Users/rfs/Downloads/datou/split_results'

def main():
    print(f"开始处理文件 (强力容错模式)...")
    
    try:
        # 1. 使用 open 的 errors='replace' 先清理数据流中的坏字节
        # 这是绕过 UnicodeDecodeError 的终极武器
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            print("正在解析内存中的数据...")
            df = pd.read_csv(f, low_memory=False)
            
        print(f"✅ 读取成功！总行数: {len(df)}")

        # 2. 检查输出路径
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 3. 按照第一列分组
        first_col = df.columns[0]
        grouped = df.groupby(first_col)
        
        total = len(grouped)
        print(f"检测到 {total} 个分类，准备写入...")

        # 4. 循环写入
        for i, (name, group) in enumerate(grouped):
            # 过滤掉文件名非法字符
            safe_name = "".join([c for c in str(name) if c.isalnum() or c in (' ', '-', '_')]).strip()
            if not safe_name: safe_name = "未知分类"
            
            output_path = os.path.join(output_dir, f"明细-{safe_name}.csv")
            
            # 统一使用 utf-8-sig，确保 Excel 打开不乱码
            group.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"进度: {i + 1}/{total}...")

        print(f"\n🎉 处理大功告成！\n输出文件夹：{output_dir}")

    except Exception as e:
        print(f"❌ 运行过程中发生错误: {e}")

if __name__ == "__main__":
    main()