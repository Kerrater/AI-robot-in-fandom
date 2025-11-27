import os
import time
import re
import requests # 确保导入 requests
from datetime import datetime, timedelta, timezone

# 确保 ai_service.py 在同一目录下
from ai_service import get_glm_response_v8 as get_ai_reply

# ======================================================================
#                            【Fandom 配置项】
#                             (从环境变量中读取)
# ======================================================================

# ❗ 安全获取：从 GitHub Secrets 中读取用户名和密码
BOT_USERNAME = os.environ.get('FANDOM_BOT_USERNAME') 
BOT_PASSWORD = os.environ.get('FANDOM_BOT_PASSWORD') 

# Fandom Wiki 的域名和页面标题
WIKI_DOMAIN = 'darkrooms.fandom.com/zh' 
CHAT_PAGE_TITLE = '暗竹聊天（测试）' 

API_URL = f'https://{WIKI_DOMAIN}/api.php'

if not all([BOT_USERNAME, BOT_PASSWORD]):
    raise ValueError("Fandom 机器人用户名或密码缺失，请检查 GitHub Secrets 和 YAML 配置。")

# ======================================================================
#                            【Fandom API 占位函数】
# ❗❗❗ 替换说明：将以下 3 个函数替换为您原有的、可用的 Fandom 登录、
# ❗❗❗           获取评论和发布回复的 Python 代码块。
# ======================================================================

def login(username, password, domain):
    print(f"--- 尝试登录 Fandom Wiki: {username} ---")
    # 替换此处的代码：使用 requests 登录 Fandom Wiki
    # 必须返回一个有效的 requests.Session() 对象
    # 示例:
    # session = requests.Session()
    # token = session.get(API_URL, params={'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}).json()['query']['tokens']['logintoken']
    # session.post(API_URL, data={'action': 'login', 'lgname': username, 'lgpassword': password, 'lgtoken': token, 'format': 'json'})
    # if check_login_status(session): return session
    # else: return None
    
    # 占位符（请删除此行和上面所有注释，并粘贴您的代码）
    return None 

def get_last_comment(session, page_title):
    print(f"--- 尝试获取页面最新评论: {page_title} ---")
    # 替换此处的代码：使用 session 对象获取页面上的最新评论文本
    # 必须返回一个字符串，如果没发现新评论，可以返回 None 或空字符串
    # 示例:
    # response = session.get(API_URL, params={...})
    # if new_comment_found: return extracted_comment_text
    # else: return ""
    
    # 占位符（请删除此行和上面所有注释，并粘贴您的代码）
    return "" 

def post_reply(session, page_title, reply_text):
    print(f"--- 尝试发布回复: 内容长度 {len(reply_text)} ---")
    # 替换此处的代码：使用 session 对象发布回复到目标页面
    # 示例:
    # edit_token = get_edit_token(session, page_title)
    # session.post(API_URL, data={'action': 'edit', 'text': reply_text, 'token': edit_token, ...})
    
    # 占位符（请删除此行和上面所有注释，并粘贴您的代码）
    pass

# ======================================================================
#                            【主任务函数】
# ======================================================================

def run_main_task():
    """GitHub Actions 单次运行的主入口点。"""
    
    # 1. 登录 Fandom
    session = login(BOT_USERNAME, BOT_PASSWORD, WIKI_DOMAIN)
    
    if not session:
        print("❌ 登录失败或 login 函数返回 None，终止任务。")
        return
    
    # 2. 检查最新评论
    user_comment = get_last_comment(session, CHAT_PAGE_TITLE)
    
    if user_comment and user_comment.strip(): 
        # 3. 调用 AI 服务获取回复
        print(f"【主任务】-> 发现新评论，调用 AI 服务...")
        ai_reply_text = get_ai_reply(user_comment) 
        
        print(f"【主任务】-> AI 回复结果: {ai_reply_text}")

        if not ai_reply_text.startswith("❌"):
            # 4. 发布回复
            post_reply(session, CHAT_PAGE_TITLE, ai_reply_text)
            print("【主任务】-> ✅ 任务成功完成：已发布回复。")
        else:
            print(f"【主任务】-> ❌ AI 生成回复失败，不发布。")
            
    else:
        print("【主任务】-> 未发现新评论或评论为空，本次任务结束。")
        

if __name__ == "__main__":
    print(f"==================================================")
    print(f"🤖 Fandom Bot (GitHub Actions 单次运行) 启动...")
    print(f"==================================================")
    run_main_task()
