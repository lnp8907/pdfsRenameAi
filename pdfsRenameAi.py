# -*- coding: utf-8 -*-
from pdf2docx import Converter
from docx import Document
import os 
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import unicodedata


# 指定包含PDF文件的文件夾路徑
folder_path = r'input'
# 指定輸出Word文件的文件夾路徑
output_folder_path = os.path.join('output', 'word')
# 設置日志目錄
log_directory = os.path.join('output', 'log')
# 等待時間，單位為秒
WAIT_TIME = 1

# 確保日志目錄存在
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# 設置日志文件名為當前時間
current_time = datetime.now().strftime('%Y%m%d%H%M%S')
log_filename = os.path.join(log_directory, f'{current_time}.log')

def convert_pdf_to_docx(pdf_file, docx_file):
    """將單個PDF文件轉換為Word文檔"""
    cv = Converter(pdf_file)
    cv.convert(docx_file, start=0, end=1)  # 轉換第一頁
    cv.close()
    # logging.info(f'已轉換: {pdf_file} 到 {docx_file}')
    return docx_file

def read_docx(docx_file):
    """讀取Word文檔內容為純文本"""
    doc = Document(docx_file)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)


def process_files_and_rename(pdf_file, docx_file):
    """讀取PDF文件，轉換為Word文檔，並為該PDF文件重命名"""
    docx_file = convert_pdf_to_docx(pdf_file, docx_file)
    text = read_docx(docx_file)
    # 這里調用OpenAI API，需要您根據實際API填充
    new_filename = call_openai_api(text)
    if new_filename:
        # 以下代碼假設為重命名邏輯的占位符
        new_pdf_path = os.path.join('output', new_filename + '.pdf')

        try:
            os.rename(pdf_file, new_pdf_path)
        except Exception as e:
            # 嘗試調用 avoid_special_characters 函數處理該異常
            handle_file_not_found_error(pdf_file, new_filename)

        logging.info(f'成功空將: {os.path.basename(pdf_file)}')
        logging.info(f'重命名為: {new_filename}')
    else:
        logging.error(f'重命名 {os.path.basename(pdf_file)} 失敗, 未能組出新名稱')

def call_openai_api(text):
    """調用OpenAI API以獲取信息"""
    api_key = os.getenv("OPENAI_API_KEY")  # 從環境變量獲取API密鑰
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You will be provided with a part of an article, Please provide the title, author. If unknown, leave it as an empty string and respond in the language of the article. Return in JSON format.",
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    
    if response.status_code == 200:
        response_data = response.json()
        # 解析API返回的數據
        content = response_data['choices'][0]['message']['content']
        # 將content字符串轉換為字典
        data_dict = json.loads(content)
        # logging.info(data_dict)
        return query_citation(data_dict)
    else:
        logging.error(f"Openai API請求失敗，狀態碼：{response.status_code}")

def fetch_and_parse(title_query, creator_query):
    # 對查詢條件進行 URL 編碼
    encoded_title = quote(title_query)
    encoded_creator = quote(creator_query)
    # 構造 URL
    url = "https://cir.nii.ac.jp/all?q=" + encoded_title
    if encoded_creator:
        # 有作者則加上作者檢索條件
        url += "&creator=" + encoded_creator
    # 發送 GET 請求
    response = requests.get(url)

    if response.status_code == 200:
        # 解析 HTML 內容
        soup = BeautifulSoup(response.text, 'html.parser')
        # 返回解析結果
        return soup
    elif  response.status_code == 429:
        time.sleep(WAIT_TIME)
        return fetch_and_parse(title_query, creator_query)
    else:
        logging.error(f"Request failed with status code: {response.status_code}")
        logging.error(f"Request URL: {url}")
        return None
        
def fetch_metadata(url):
    # 發送 GET 請求並獲取網頁內容
    response = requests.get(url)
    html_content = response.text
    
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到所有以 citation_ 開頭的 meta 標簽
    meta_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('citation_')})
    
    # 創建一個空的字典來存儲元數據
    metadata = {}

    # 提取屬性名和屬性值，並存儲到 metadata 字典中
    for tag in meta_tags:
        key = tag['name'].replace('citation_', '', 1)
        value = tag['content']
        metadata[key] = value
    
    return metadata

def format_citation(metadata):
    # 提取元數據中的相應字段
    author = metadata.get('author', '')
    year = metadata.get('date', '').split('-')[0]  # 從日期中提取年份
    title = metadata.get('title', '')
    journal = metadata.get('journal_title', '')
    volume = metadata.get('volume', '')
    issue = metadata.get('issue', '')
    start_page = metadata.get('firstpage', '')
    end_page = metadata.get('lastpage', '')

    # 格式化引用字符串
    if issue:
        issue = f'（{issue}）'
    citation = f'{author}, {year}, 「{title}」{journal}{issue}{volume}, p.{start_page}-{end_page}'
    
    return citation

def query_citation(data_dict):
    title = data_dict.get('title', '')
    author = data_dict.get('author', '')
    # first_ten_chars = title[:10] if len(title) > 10 else title
    # 添加延遲
    parsed_html = fetch_and_parse(title, author)
    
    # 提取鏈接和標題
    if parsed_html:
       # 查找第一個匹配項
        first_item = parsed_html.select_one('div.listitem.xfolkentry')
        if first_item:
            # 提取鏈接和標題
            link_element = first_item.select_one('a.taggedlink')
            if link_element:
                link = 'https://cir.nii.ac.jp' + link_element['href']

            title_element = first_item.select_one('dl.paper_class > dt.item_mainTitle.item_title > a')
            if title_element:
                title = title_element.get_text(strip=True)

            # 獲取詳細頁數據
            metadata = fetch_metadata(link)
            
            # 格式化引用字符串
            citation = format_citation(metadata)

            # 輸出引用字符串
            return citation
            
        else:
            logging.error(f"未找檢索到相關論文-> 作者:{author}, 標題開頭:{title}")
            return None

def half_to_full_punctuation(text):
    full_punctuation = {
        '!': '！',
        '"': '＂',
        '#': '＃',
        '$': '＄',
        '%': '％',
        '&': '＆',
        '\'': '＇',
        '(': '（',
        ')': '）',
        '*': '＊',
        '+': '＋',
        ',': '，',
        '-': '－',
        '.': '．',
        '/': '／',
        ':': '：',
        ';': '；',
        '<': '＜',
        '=': '＝',
        '>': '＞',
        '?': '？',
        '@': '＠',
        '[': '［',
        '\\': '＼',
        ']': '］',
        '^': '＾',
        '_': '＿',
        '`': '｀',
        '{': '｛',
        '|': '｜',
        '}': '｝',
        '~': '～',
        '｢': '「',
        '｣': '」',
        '『': '『', 
        '』': '』',
    }

    full_text = ''
    for char in text:
        if char in full_punctuation:
            full_text += full_punctuation[char]
        else:
            full_text += char

    return full_text

def avoid_special_characters(filename):
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, ' ')
    return filename

def handle_file_not_found_error(pdf_file, filename):
    try:
        # 嘗試調用 avoid_special_characters 函數
        logging.warning(f"新名稱恐含有特殊字元，特殊名稱:{filename}")
        new_filename = avoid_special_characters(filename)
        new_pdf_path = os.path.join('output', new_filename + '.pdf')
        logging.info(f"已將特殊字元替換為空格:{os.path.basename(new_filename)}")
        # 如果調用成功，嘗試重命名文件
        os.rename(pdf_file, new_pdf_path)
    except Exception as e:
        # 如果遇到異常，則記錄錯誤日志，但不中斷程序繼續執行
        logging.error(f"重新命名失敗：{e}")

def main():
    # 配置日志記錄器
    logging.basicConfig(filename=log_filename, level=logging.INFO, 
                        format='%(asctime)s:%(levelname)s:%(message)s')
    # 獲取PDF文件列表
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        # 構造PDF文件和對應的DOCX文件路徑
        pdf_path = os.path.join(folder_path, pdf_file)
        docx_file = os.path.join(output_folder_path, os.path.splitext(pdf_file)[0] + '.docx')
        # 處理PDF文件並重命名
        process_files_and_rename(pdf_path, docx_file)
    
    # 清空 word 文件夾
    for file in os.listdir(output_folder_path):
        file_path = os.path.join(output_folder_path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logging.error(f"Error deleting file: {e}")
    logging.shutdown()
# 執行主程式
main() 
