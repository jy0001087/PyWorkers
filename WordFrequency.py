import os
import re
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from docx import Document
from bs4 import BeautifulSoup
import zipfile

# 确保已经下载了nltk的数据
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('punkt_tab')


def process_word_documents(word_dir, total_word_freq):
    """
    处理Word文档，统计单词频次并更新总的频次计数器
    :param word_dir: Word文档所在目录
    :param total_word_freq: 总的单词频次计数器
    :return: 更新后的总的单词频次计数器
    """
    lemmatizer = WordNetLemmatizer()
    for filename in os.listdir(word_dir):
        if filename.endswith('.docx'):
            file_path = os.path.join(word_dir, filename)
            doc = Document(file_path)
            text = []
            for para in doc.paragraphs:
                clean_text = re.sub(r'[^\w\s]', '', para.text).lower()
                text.append(clean_text)
            full_text = ' '.join(text)
            words = word_tokenize(full_text)
            lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
            total_word_freq.update(lemmatized_words)
    return total_word_freq


def process_epub_documents(epub_dir, log_path, total_word_freq):
    lemmatizer = WordNetLemmatizer()
    for filename in os.listdir(epub_dir):
        if filename.endswith('.epub'):
            file_path = os.path.join(epub_dir, filename)
            with zipfile.ZipFile(file_path) as zf:
                # 在epub中，通常HTML文件包含文本内容，这里假设所有HTML文件都有文本需要处理
                for name in zf.namelist():
                    if name.endswith('.html'):
                        with zf.open(name) as f:
                            content = f.read()
                            soup = BeautifulSoup(content, 'html.parser')
                            body = soup.find('body')
                            if body:
                                text = body.get_text(separator=' ')
                                clean_text = re.sub(r'[^\w\s]', '', text).lower()
                                words = word_tokenize(clean_text)
                                lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
                                total_word_freq.update(lemmatized_words)
    return total_word_freq


def write_word_frequency_to_log(log_path, total_word_freq):
    """
    将单词频次结果写入日志文件
    :param log_path: 日志文件路径
    :param total_word_freq: 总的单词频次计数器
    """
    with open(log_path, 'a', encoding='utf-8') as log_file:
        for word, freq in total_word_freq.most_common():
            log_file.write(f"{word}: {freq}\n")


if __name__ == '__main__':
    # 初始化词形还原器
    lemmatizer = WordNetLemmatizer()
    # 指定Word文档所在的目录和输出日志文件的路径
    word_dir = r'F:\Julius\Documents\词频统计'
    epub_dir = r'F:\Julius\Documents\词频统计'
    log_path = r'F:\Julius\Documents\词频统计\result.log'
    # 用于存储所有文档的单词频次
    total_word_freq = Counter()

    total_word_freq = process_word_documents(word_dir, total_word_freq)
    total_word_freq = process_epub_documents(epub_dir, log_path, total_word_freq)
    write_word_frequency_to_log(log_path, total_word_freq)

    print(f"Word frequency has been written to {log_path}")
