import os
import argparse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_text_from_html(html_content):
    """从 HTML 内容中提取文本，保留基本格式"""
    try:
        # 移除 XML 声明和命名空间
        html_content = html_content.replace('<?xml version="1.0" encoding="utf-8"?>', '')
        
        # 解析 HTML
        root = ET.fromstring(f'<root>{html_content}</root>')
    except ET.ParseError:
        # 如果解析失败，尝试用正则表达式处理
        import re
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html_content)
        # 移除多余空白
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    text_parts = []
    
    def parse_element(elem, level=0):
        """递归解析 XML 元素"""
        # 处理文本内容
        if elem.text:
            text = elem.text.strip()
            if text:
                # 根据标签类型添加格式
                if elem.tag.endswith(('h1', 'h2', 'h3', 'h4', 'h5', 'h6')):
                    level_num = int(elem.tag[-1])
                    text_parts.append('\n' + '=' * (level_num - 1) + ' ' + text + ' ' + '=' * (level_num - 1) + '\n')
                elif elem.tag.endswith(('p', 'div')):
                    text_parts.append(text + '\n')
                elif elem.tag.endswith('li'):
                    text_parts.append('  • ' + text + '\n')
                elif elem.tag.endswith(('strong', 'b')):
                    text_parts.append('**' + text + '**')
                elif elem.tag.endswith(('em', 'i')):
                    text_parts.append('_' + text + '_')
                else:
                    text_parts.append(text)
        
        # 递归处理子元素
        for child in elem:
            parse_element(child, level + 1)
            # 处理子元素后的尾部文本
            if child.tail:
                tail_text = child.tail.strip()
                if tail_text:
                    text_parts.append(tail_text)
    
    parse_element(root)
    result = ''.join(text_parts)
    # 清理多余空行
    result = '\n'.join(line for line in result.split('\n') if line.strip() or result.split('\n').index(line) == 0)
    return result.strip()

def extract_xhtml_content(epub_path):
    """从 EPUB 文件中提取所有 XHTML 内容"""
    all_text = []
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            # 获取 container.xml 找到 OPF 文件
            try:
                container_xml = zip_ref.read('META-INF/container.xml').decode('utf-8')
                root = ET.fromstring(container_xml)
                
                # 查找 OPF 文件路径
                namespaces = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                opf_path = root.find('.//container:rootfile', namespaces).get('full-path')
            except:
                # 如果没有 container.xml，尝试找 content.opf
                opf_path = None
                for name in zip_ref.namelist():
                    if name.endswith('.opf'):
                        opf_path = name
                        break
            
            if not opf_path:
                raise Exception("未找到 OPF 文件")
            
            # 解析 OPF 文件获取清单
            opf_content = zip_ref.read(opf_path).decode('utf-8')
            opf_root = ET.fromstring(opf_content)
            
            # 定义命名空间
            namespaces = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # 获取 spine（阅读顺序）
            spine = opf_root.find('.//opf:spine', namespaces)
            if spine is None:
                raise Exception("未找到 spine 元素")
            
            # 获取清单映射
            manifest = {}
            for item in opf_root.findall('.//opf:item', namespaces):
                manifest[item.get('id')] = {
                    'href': item.get('href'),
                    'media_type': item.get('media-type')
                }
            
            # 按 spine 顺序读取内容
            for itemref in spine.findall('opf:itemref', namespaces):
                item_id = itemref.get('idref')
                if item_id in manifest:
                    item_info = manifest[item_id]
                    # 只处理 XHTML 内容
                    if 'xhtml' in item_info['media_type'] or 'html' in item_info['media_type']:
                        # 构造相对路径
                        opf_dir = os.path.dirname(opf_path)
                        content_path = os.path.join(opf_dir, item_info['href']).replace('\\', '/')
                        
                        try:
                            html_content = zip_ref.read(content_path).decode('utf-8')
                            text = extract_text_from_html(html_content)
                            if text:
                                all_text.append(text)
                                all_text.append('\n' + '-' * 40 + '\n')  # 章节分隔符
                        except Exception as e:
                            print(f"[ERROR] 读取 {content_path} 失败: {e}")
    
    except zipfile.BadZipFile:
        raise Exception(f"{epub_path} 不是有效的 EPUB 文件")
    except Exception as e:
        raise Exception(f"解析 EPUB 失败: {e}")
    
    return '\n'.join(all_text)

def convert_epub_to_txt(epub_path, output_path=None):
    """将 EPUB 转换为 TXT"""
    epub_path = os.path.expanduser(epub_path)
    
    # 验证输入文件
    if not os.path.exists(epub_path):
        print(f"[ERROR] 文件不存在: {epub_path}")
        return False
    
    if not epub_path.lower().endswith('.epub'):
        print(f"[ERROR] 不是 EPUB 文件: {epub_path}")
        return False
    
    # 确定输出路径
    if output_path is None:
        output_path = os.path.splitext(epub_path)[0] + '.txt'
    else:
        output_path = os.path.expanduser(output_path)
    
    try:
        print(f"[START] 开始转换: {epub_path}")
        
        # 提取文本
        text_content = extract_xhtml_content(epub_path)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"[DONE] 转换完成: {output_path}")
        print(f"[INFO] 文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
        return True
    
    except Exception as e:
        print(f"[ERROR] 转换失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='EPUB 转 TXT 工具')
    parser.add_argument('--epub', required=True, help='输入 EPUB 文件路径')
    parser.add_argument('--output', help='输出 TXT 文件路径（可选，默认在同目录）')
    
    args = parser.parse_args()
    
    convert_epub_to_txt(args.epub, args.output)

if __name__ == '__main__':
    main()