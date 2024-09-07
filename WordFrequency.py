import os
import re
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from docx import Document
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

## pip install python-docx nltk

# 确保已经下载了nltk的数据
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('punkt_tab')

# 初始化词形还原器
lemmatizer = WordNetLemmatizer()

# 指定Word文档所在的目录和输出日志文件的路径
word_dir = r'F:\Julius\Documents\词频统计'
epub_dir = r'F:\Julius\Documents\词频统计'
log_path = r'F:\Julius\Documents\词频统计\result.log'

# 用于存储所有文档的单词频次
total_word_freq = Counter()

# 遍历目录中的所有Word文档
for filename in os.listdir(word_dir):
    if filename.endswith('.docx'):
        file_path = os.path.join(word_dir, filename)
        doc = Document(file_path)
        text = []

        # 读取文档内容
        for para in doc.paragraphs:
            # 移除标点符号并转换为小写
            clean_text = re.sub(r'[^\w\s]', '', para.text).lower()
            text.append(clean_text)

        # 合并所有段落的文本
        full_text = ' '.join(text)

        # 分词
        words = word_tokenize(full_text)

        # 词形还原
        lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

        # 更新总的单词频次计数器
        total_word_freq.update(lemmatized_words)

with open(log_path, 'w', encoding='utf-8') as log_file:
# 遍历目录中的所有EPUB文件
    for filename in os.listdir(epub_dir):
        if filename.endswith('.epub'):
            file_path = os.path.join(epub_dir, filename)
            book = epub.read_epub(file_path)
            text = []

        # 读取EPUB文件中的所有文本
            # 遍历EPUB中的所有章节
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # 使用item.get_name()获取章节标题
                title = item.get_name()
                log_file.write(f'Chapter: {title}\n')
            
                # 获取章节内容
                content = item.get_content().decode('utf-8')
                        # 移除标点符号并转换为小写
                content = BeautifulSoup(content,features="xml").get_text()
                clean_text = re.sub(r'[^\w\s]', '', content).lower()
                text.append(clean_text)

            # 合并所有章节的文本
            full_text = ' '.join(text)

            log_file.write(f"EPUB文件: {filename}\n")
            log_file.write(full_text + "\n\n")

            # 分词
            words = word_tokenize(full_text)

            # 词形还原
            lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

            # 更新总的单词频次计数器
            total_word_freq.update(lemmatized_words)

# 将结果写入日志文件
with open(log_path, 'a', encoding='utf-8') as log_file:
    for word, freq in total_word_freq.most_common():
        log_file.write(f"{word}: {freq}\n")

print(f"Word frequency has been written to {log_path}")