# 基础用法（默认黑色边框 30px）
# python addPhoneFrame.py --input /path/to/images

# 指定边框宽度
# python addPhoneFrame.py --input /path/to/images --frame-width 50

# 指定边框颜色（白色）
# python addPhoneFrame.py --input /path/to/images --frame-color 255 255 255

# 添加刘海设计
# python addPhoneFrame.py --input /path/to/images --with-notch

# 指定输出目录
# python addPhoneFrame.py --input /path/to/images --output /output/path --frame-width 40

# 完整示例
# python addPhoneFrame.py --input ~/Pictures/photos --output ~/Pictures/framed --frame-width 35 --frame-color 50 50 50 --with-notch

import os
import argparse
from PIL import Image, ImageDraw
from pathlib import Path

def create_phone_frame(image_path, output_path, frame_width=30, frame_color=(0, 0, 0), corner_radius=50):
    """
    为图片添加手机外壳边框（内外都有圆角）
    """
    try:
        # 打开原始图片
        img = Image.open(image_path)
        
        # 转换为 RGB（如果是 RGBA）
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # 获取原始图片尺寸
        orig_width, orig_height = img.size
        
        # 计算新图片尺寸
        new_width = orig_width + frame_width * 2
        new_height = orig_height + frame_width * 2
        
        # 1. 为原始图片添加圆角
        img_rounded = img.convert('RGBA')
        img_mask = Image.new('L', (orig_width, orig_height), 0)
        img_mask_draw = ImageDraw.Draw(img_mask)
        inner_radius = min(corner_radius - 5, 40)
        img_mask_draw.rounded_rectangle(
            [0, 0, orig_width - 1, orig_height - 1],
            radius=inner_radius,
            fill=255
        )
        img_rounded.putalpha(img_mask)
        
        # 2. 创建带圆角的最终图片
        final = Image.new('RGBA', (new_width, new_height), (*frame_color, 255))
        
        # 3. 为最终图片添加外圆角掩膜
        final_mask = Image.new('L', (new_width, new_height), 0)
        final_mask_draw = ImageDraw.Draw(final_mask)
        final_mask_draw.rounded_rectangle(
            [0, 0, new_width - 1, new_height - 1],
            radius=corner_radius,
            fill=255
        )
        final.putalpha(final_mask)
        
        # 4. 在中心粘贴圆角图片
        final.paste(img_rounded, (frame_width, frame_width), img_rounded)
        
        # 保存为 PNG 格式
        output_path_png = os.path.splitext(output_path)[0] + '.png'
        final.save(output_path_png, 'PNG')
        
        print(f"[DONE] {os.path.basename(image_path)} -> {os.path.basename(output_path_png)}")
        return True
    
    except Exception as e:
        print(f"[ERROR] 处理失败 {image_path}: {e}")
        return False

def create_phone_frame_with_notch(image_path, output_path, frame_width=30, frame_color=(0, 0, 0), corner_radius=50):
    """
    为图片添加手机外壳边框（带刘海、内外都有圆角）
    """
    try:
        # 打开原始图片
        img = Image.open(image_path)
        
        # 转换为 RGB
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # 获取原始图片尺寸
        orig_width, orig_height = img.size
        
        # 刘海尺寸
        notch_width = orig_width // 3
        notch_height = frame_width // 2
        
        # 计算新图片尺寸
        new_width = orig_width + frame_width * 2
        new_height = orig_height + frame_width * 2 + notch_height
        
        # 1. 为原始图片添加圆角
        img_rounded = img.convert('RGBA')
        img_mask = Image.new('L', (orig_width, orig_height), 0)
        img_mask_draw = ImageDraw.Draw(img_mask)
        inner_radius = min(corner_radius - 5, 40)
        img_mask_draw.rounded_rectangle(
            [0, 0, orig_width - 1, orig_height - 1],
            radius=inner_radius,
            fill=255
        )
        img_rounded.putalpha(img_mask)
        
        # 2. 创建边框背景
        frame_bg = Image.new('RGB', (new_width, new_height), frame_color)
        frame_draw = ImageDraw.Draw(frame_bg)
        
        # 绘制刘海
        notch_x1 = (new_width - notch_width) // 2
        notch_y1 = frame_width
        notch_x2 = notch_x1 + notch_width
        notch_y2 = notch_y1 + notch_height
        notch_radius = notch_height // 2
        frame_draw.rounded_rectangle(
            [notch_x1, notch_y1, notch_x2, notch_y2],
            radius=notch_radius,
            fill=frame_color
        )
        
        # 3. 创建带圆角的最终图片
        final = frame_bg.convert('RGBA')
        
        # 4. 为最终图片添加外圆角掩膜
        final_mask = Image.new('L', (new_width, new_height), 0)
        final_mask_draw = ImageDraw.Draw(final_mask)
        final_mask_draw.rounded_rectangle(
            [0, 0, new_width - 1, new_height - 1],
            radius=corner_radius,
            fill=255
        )
        final.putalpha(final_mask)
        
        # 5. 在中心粘贴圆角图片
        final.paste(img_rounded, (frame_width, frame_width + notch_height), img_rounded)
        
        # 保存为 PNG 格式
        output_path_png = os.path.splitext(output_path)[0] + '.png'
        final.save(output_path_png, 'PNG')
        
        print(f"[DONE] {os.path.basename(image_path)} -> {os.path.basename(output_path_png)}")
        return True
    
    except Exception as e:
        print(f"[ERROR] 处理失败 {image_path}: {e}")
        return False

def batch_process_images(input_dir, output_dir=None, frame_width=30, frame_color=(0, 0, 0), with_notch=False, corner_radius=50):
    """
    批量处理目录下的所有图片
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录（可选，默认在输入目录下创建 framed_images）
        frame_width: 边框宽度
        frame_color: 边框颜色
        with_notch: 是否添加刘海
        corner_radius: 圆角半径
    """
    input_dir = os.path.expanduser(input_dir)
    
    # 验证输入目录
    if not os.path.isdir(input_dir):
        print(f"[ERROR] 目录不存在: {input_dir}")
        return False
    
    # 确定输出目录
    if output_dir is None:
        output_dir = os.path.join(input_dir, 'framed_images')
    else:
        output_dir = os.path.expanduser(output_dir)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
    
    # 获取所有图片文件
    image_files = [
        f for f in os.listdir(input_dir)
        if os.path.isfile(os.path.join(input_dir, f)) and 
           os.path.splitext(f)[1].lower() in image_extensions
    ]
    
    if not image_files:
        print(f"[WARNING] 目录下没有找到图片文件: {input_dir}")
        return False
    
    print(f"[START] 开始处理 {len(image_files)} 张图片")
    print(f"[CONFIG] 边框宽度: {frame_width}px, 颜色: {frame_color}, 圆角: {corner_radius}px, 刘海: {with_notch}")
    
    # 处理每张图片
    success_count = 0
    for filename in image_files:
        input_path = os.path.join(input_dir, filename)
        
        # 生成输出文件名（添加前缀）
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_framed{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # 选择处理函数
        if with_notch:
            if create_phone_frame_with_notch(input_path, output_path, frame_width, frame_color, corner_radius):
                success_count += 1
        else:
            if create_phone_frame(input_path, output_path, frame_width, frame_color, corner_radius):
                success_count += 1
    
    print(f"[SUMMARY] 成功处理 {success_count}/{len(image_files)} 张图片")
    print(f"[OUTPUT] 输出目录: {output_dir}")
    return True

def main():
    parser = argparse.ArgumentParser(description='为图片添加手机外壳边框（大圆角）')
    parser.add_argument('--input', required=True, help='输入目录路径')
    parser.add_argument('--output', help='输出目录路径（可选，默认在输入目录下创建 framed_images）')
    parser.add_argument('--frame-width', type=int, default=30, help='边框宽度（像素），默认 30')
    parser.add_argument('--corner-radius', type=int, default=50, help='圆角半径（像素），默认 50')
    parser.add_argument('--frame-color', nargs=3, type=int, default=[0, 0, 0], 
                        help='边框颜色 RGB 值，默认黑色 (0 0 0)，例如: --frame-color 255 255 255')
    parser.add_argument('--with-notch', action='store_true', help='添加刘海设计')
    
    args = parser.parse_args()
    
    frame_color = tuple(args.frame_color)
    batch_process_images(
        args.input,
        args.output,
        frame_width=args.frame_width,
        frame_color=frame_color,
        with_notch=args.with_notch,
        corner_radius=args.corner_radius
    )

if __name__ == '__main__':
    main()