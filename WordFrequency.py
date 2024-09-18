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
       lemmatizer = WordNetLemmatizer()
       stop_words = set(stopwords.words('english'))
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
               # 过滤停用词
               filtered_words = [word for word in words if word not in stop_words]
               lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
               total_word_freq.update(lemmatized_words)
       return total_word_freq


def process_epub_documents(epub_dir, log_path, total_word_freq):
       lemmatizer = WordNetLemmatizer()
       stop_words = set(stopwords.words('english'))
       for filename in os.listdir(epub_dir):
           if filename.endswith('.epub'):
               file_path = os.path.join(epub_dir, filename)
               with zipfile.ZipFile(file_path) as zf:
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
                                   # 过滤停用词
                                   filtered_words = [word for word in words if word not in stop_words]
                                   lemmatized_words = [lemmatizer.lemmatize(word) for word in filtered_words]
                                   total_word_freq.update(lemmatized_words)
       return total_word_freq


def write_word_frequency_to_log(log_path, total_word_freq):
       with open(log_path, 'w', encoding='utf - 8') as log_file:
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
