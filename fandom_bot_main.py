import os
import requests
import json
import time
import re

# 导入 AI 核心服务模块
# 确保此处的别名与 ai_service.py 中的函数名 get_glm_response_v8 对应
from ai_service import get_glm_response_v8 as get_ai_reply 

# ======================================================================
#                            【Fandom 配置项】
# ======================================================================

# !!! 从环境变量中读取敏感信息 !!!
BOT_USERNAME = os.environ.get('FANDOM_BOT_USERNAME', 'Kerrater@Dark_Zhu_KerVs')
BOT_PASSWORD = os.environ.get('FANDOM_BOT_PASSWORD') 

if not BOT_PASSWORD:
    raise ValueError("环境变量 FANDOM_BOT_PASSWORD 缺失，请配置后再运行。")

WIKI_DOMAIN = os.environ.get('FANDOM_WIKI_DOMAIN', 'darkrooms.fandom.com/zh')
CHAT_PAGE_TITLE = os.environ.get('FANDOM_CHAT_PAGE', '暗竹聊天（测试）') 

API_URL = f'https://{WIKI_DOMAIN}/api.php'
GENERIC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# ======================================================================
#                         【Fandom 交互函数】
# ======================================================================

def call_api(session, data):
    """向 MediaWiki API 发送 POST/GET 请求并返回 JSON 结果，使用模拟 User-Agent"""
    headers = {'User-Agent': GENERIC_USER_AGENT}
    method = 'POST' if 'action' in data and data['action'] in ['login', 'edit'] else 'GET'
    
    if method == 'POST':
        response = session.post(API_URL, data=data, headers=headers)
    else:
        response = session.get(API_URL, params=data, headers=headers)
        
    response.raise_for_status()
    return response.json()

def login_fandom(session):
    """执行登录操作，包括获取令牌和发送登录请求"""
    print(f"[Fandom Bot] -> 正在登录用户: {BOT_USERNAME}...")
    
    # 步骤 1: 获取登录令牌
    login_token_data = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
    token_result = call_api(session, login_token_data)
    login_token = token_result['query']['tokens']['logintoken']

    # 步骤 2: 发送登录请求
    login_data = {
        'action': 'login',
        'lgname': BOT_USERNAME,
        'lgpassword': BOT_PASSWORD,
        'lgtoken': login_token,
        'format': 'json'
    }
    
    login_result = call_api(session, login_data)

    if 'login' in login_result and login_result['login']['result'] == 'Success':
        print("[Fandom Bot] -> ✅ 登录成功。")
        return True
    else:
        print(f"[Fandom Bot] -> ❌ 登录失败。错误信息: {login_result.get('login', {}).get('reason', '未知错误')}")
        return False

def get_csrf_token(session):
    """获取 CSRF 编辑令牌"""
    print("[Fandom Bot] -> 获取编辑令牌...")
    token_data = {
        'action': 'query',
        'meta': 'tokens',
        'type': 'csrf',
        'format': 'json'
    }
    token_result = call_api(session, token_data)
    return token_result['query']['tokens']['csrftoken']

def get_page_content(session, title):
    """获取指定页面的当前内容"""
    query_data = {
        'action': 'query',
        'prop': 'revisions',
        'titles': title,
        'rvprop': 'content',
        'formatversion': 2,
        'format': 'json'
    }
    result = call_api(session, query_data)
    
    pages = result.get('query', {}).get('pages', [])
    if pages and 'revisions' in pages[0]:
        return pages[0]['revisions'][0]['content']
    return ""

def edit_page_replace(session, title, new_content, token, summary="Bot update"):
    """替换整个页面的内容，并检查是否需要重新登录。"""
    print(f"[Fandom Bot] -> 正在提交编辑到页面 '{title}' (模拟用户模式)...")
    edit_data = {
        'action': 'edit',
        'title': title,
        'text': new_content, 
        'token': token,
        'summary': summary,
        'format': 'json'
    }
    
    try:
        edit_result = call_api(session, edit_data)
    except requests.exceptions.RequestException as e:
        print(f"[Fandom Bot] -> ❌ API 网络请求失败: {e}")
        return False

    if 'edit' in edit_result and edit_result['edit']['result'] == 'Success':
        print("[Fandom Bot] -> ✅ 编辑成功。")
        return True
    else:
        error_info = edit_result.get('error', {})
        error_code = error_info.get('code')
        if error_code in ['badtoken', 'notloggedin']:
            print(f"[Fandom Bot] -> ❌ 编辑失败：{error_code}。会话可能已过期，需要重新登录。")
            return 'RELOG_REQUIRED' 
            
        print(f"[Fandom Bot] -> ❌ 编辑失败。{json.dumps(edit_result, indent=2)}")
        return False

# ======================================================================
#                 【主逻辑：单次任务执行 (GitHub Actions 适用)】
# ======================================================================
def main_chat_task(session, token):
    """单次任务逻辑：检查新消息并回复一次"""
    
    print(f"\n[GitHub Actions] -> 正在执行单次检查任务...")
    
    try:
        current_content = get_page_content(session, CHAT_PAGE_TITLE) or ""
    except Exception as e:
        print(f"[GitHub Actions] -> ❌ 获取页面内容失败，跳过本次任务: {e}")
        return
    
    # 查找 <start>...<end> 标记
    match = re.search(r'<start>(.*?)<end>', current_content, re.DOTALL | re.IGNORECASE)

    if match:
        user_comment = match.group(1).strip()
        if user_comment:
            print(f"[Main Task] -> 提取到用户输入:\n-----\n{user_comment}\n-----")

            # 调用 AI 服务
            ai_reply_text = get_ai_reply(user_comment)

            if ai_reply_text and not ai_reply_text.startswith("❌"):
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                fandom_reply = f"\n* 在 {timestamp}，暗竹回复：{ai_reply_text}\n"
                
                full_match_text = match.group(0)
                
                # 替换 <start>...<end> 标记为回复内容
                new_content_with_reply = current_content.replace(
                    full_match_text, 
                    f"{user_comment}\n{fandom_reply}", 
                    1 
                )

                edit_summary = "回复用户并清理<start><end>标记"
                edit_result = edit_page_replace(session, CHAT_PAGE_TITLE, new_content_with_reply, token, edit_summary)
                
                # === 重登录逻辑 ===
                if edit_result == 'RELOG_REQUIRED':
                    print("\n[RELOGIC] -> 检测到会话过期，尝试重新登录...")
                    
                    if login_fandom(session):
                        token = get_csrf_token(session)
                        print("[RELOGIC] -> 重新登录成功，尝试再次编辑...")
                        edit_page_replace(session, CHAT_PAGE_TITLE, new_content_with_reply, token, f"{edit_summary} (重试)")
                    else:
                        print("[RELOGIC] -> ❌ 重新登录失败。本次任务结束。")
                        
                # ======================
                    
            else:
                print(f"[Main Task] -> AI 未生成有效回复。结果: {ai_reply_text}")
                
    else:
        print("[Main Task] -> 页面无 <start>...<end> 标记。本次任务结束。")

# ======================================================================
#                  【主程序入口（GitHub Actions 调用）】
# ======================================================================
if __name__ == "__main__":
    try:
        # 初始化会话
        with requests.Session() as session:
            # 初始登录
            if not login_fandom(session):
                exit(1) # 登录失败，退出本次运行
            
            token = get_csrf_token(session)
            
            # 执行单次任务
            main_chat_task(session, token)
            
    except Exception as e:
        print(f"\n程序发生致命错误: {e}")
        exit(1)
