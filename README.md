# PDF智能重命名工具

本工具使用Python編寫，旨在自動化地將PDF文件轉換為Word文檔，通過OpenAI API提取特定信息（如作者、標題等），最後根據這些信息重新命名原始PDF文件。該工具特別適合需要批量處理PDF文檔並希望基於內容進行有意義命名的場景。

## 核心功能

- **自動化轉換**：批量將指定文件夾內的PDF文件轉換為Word格式，便於後續處理。
- **內容提取**：自動通過OpenAI API提取Word文檔中的關鍵信息，如標題、作者等。
- **智能重命名**：根據提取的信息，智能地重新命名原始PDF文件，使文件名更加有意義和易於理解。
- **並行處理**：利用並發處理提高處理效率。
- **日志記錄**：生成詳細的日志文件，記錄轉換過程和結果，便於追蹤和問題定位。

## 環境需求

- Python 3.6 或更高版本
- pip（Python包管理器）
- 有效的OpenAI API密鑰

## 安裝指南

在運行腳本之前，請確保安裝了所有必需的依賴包：

```bash
alias pip='python3.9 -m pip'
alias python='python3.9'  
pip install pdf2docx beautifulsoup4 requests
```

## 配置說明

### 設置OpenAI API密鑰

- **Windows**：
  1. 通過“系統環境變量編輯器”設置環境變量`OPENAI_API_KEY`，輸入你的OpenAI API密鑰作為變量值。

- **macOS**：
  1. 打開終端（Terminal）。
  2. 使用以下命令編輯你的shell配置文件，如`.bash_profile`或`.zshrc`：

    ```bash
    open -e ~/.bash_profile
    ```

  3. 在打開的文件中添加以下行：

    ```bash
    export OPENAI_API_KEY="你的API密鑰"
    ```

  4. 保存文件並關閉編輯器。
  5. 在終端中運行`source ~/.bash_profile`來應用更改。

### 日志文件配置

日志文件默認保存在`output/log`目錄下。你可以通過修改腳本中的`log_directory`變量來更改日志文件的保存位置。

## 使用方法

1. 將PDF文件放入`input`文件夾。
2. 運行腳本：

    ```bash
    python pdf_to_word.py
    ```

3. 腳本執行完畢後，原始PDF文件將根據從文檔中提取的信息被智能重新命名，並保存在`output`文件夾中。

## 重命名規則

重命名的文件將根據從每個PDF文檔中提取的信息（如標題、作者、年份等）來構建新的文件名，例如：“作者_年份_標題.pdf”，並保存在指定的輸出目錄中。

## 日志記錄

詳細的日志將幫助您跟蹤每個文件的處理過程和結果，包括成功轉換和重命名的文件，以及任何可能發生的錯誤。日志文件以執行腳本的日期和時間命名，方便查找和審計。

### 作者

Kenshi Chen