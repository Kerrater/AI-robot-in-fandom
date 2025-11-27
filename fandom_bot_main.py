import os
import requests
import json
import time
import re
from datetime import datetime, timezone

# 导入 AI 服务模块
from ai_service import get_glm_response_v8 as get_ai_reply 

# ======================================================================
#                            【Fandom 配置项】
#                             (从环境变量中读取)
# ======================================================================

# ❗ 安全获取：从 GitHub Secrets/ENV 中读取敏感信息
BOT_USERNAME = os.environ.get('FANDOM_BOT_USERNAME', 'Kerrater@Dark_Zhu_KerVs') 
BOT_PASSWORD = os.environ.get('FANDOM_BOT_PASSWORD') 

WIKI_DOMAIN = 'darkrooms.fandom.com/zh' 
CHAT_PAGE_TITLE = '暗竹聊天（测试）' 

API_URL = f'https://{WIKI_DOMAIN}/api.php'

if not all([BOT_USERNAME, BOT_PASSWORD]):
    # 如果缺少密码，程序应立即退出
    raise ValueError("Fandom 机器人用户名或密码缺失，请检查 GitHub Secrets 和 YAML 配置。")

# ======================================================================
#                            【Fandom 交互函数】
#                             (基于您的原有代码精简)
# ======================================================================

def call_api(session, data):
    """向 MediaWiki API 发送 POST/GET 请求并返回 JSON 结果"""
    headers = {
        'User-Agent': 'DarkroomsBot/1.1 (Contact: YourUsername; Fandom-Chat-Bot)'
    }
    method = 'POST' if 'action' in data and data['action'] in ['login', 'edit'] else 'GET'
    
    if method == 'POST':
        response = session.post(API_URL, data=data, headers=headers)
    else:
        response = session.get(API_URL, params=data, headers=headers)
        
    response.raise_for_status()
    return response.json()

def perform_login(session):
    """登录 Fandom 并返回是否成功"""
    print(f"[Fandom Bot] -> 尝试登录为用户：{BOT_USERNAME}...")

    # --- 1. 获取登录令牌 ---
    token_request_data = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
    try:
        token_result = call_api(session, token_request_data)
        login_token = token_result['query']['tokens']['logintoken']
    except Exception as e:
        print(f"[Fandom Bot] -> ❌ 获取登录令牌失败: {e}")
        return False
    
    # --- 2. 使用令牌进行实际登录 ---
    login_data = {
        'action': 'login',
        'lgname': BOT_USERNAME,
        'lgpassword': BOT_PASSWORD, # 使用 Secret 变量
        'lgtoken': login_token, 
        'format': 'json'
    }
    
    try:
        login_result = call_api(session, login_data)
        if login_result.get('login', {}).get('result') == 'Success':
            print("[Fandom Bot] -> ✅ 登录成功。")
            return True
        elif login_result.get('login', {}).get('result') == 'Failed':
            error_reason = login_result['login'].get('reason', '未知原因')
            print(f"[Fandom Bot] -> ❌ 登录失败：{error_reason}")
            return False
        else:
            print(f"[Fandom Bot] -> ⚠️ 登录 API 返回未知结果。")
            return False
    except Exception as e:
        print(f"[Fandom Bot] -> ❌ 登录过程中发生意外错误: {e}")
        return False


def get_csrf_token(session):
    """获取 CSRF 编辑令牌"""
    print("[Fandom Bot] -> 获取编辑令牌...")
    token_data = {'action': 'query', 'meta': 'tokens', 'type': 'csrf', 'format': 'json'}
    token_result = call_api(session, token_data)
    return token_result['query']['tokens']['csrftoken']

def get_page_content(session, title):
    """获取指定页面的当前内容"""
    query_data = {
        'action': 'query', 'prop': 'revisions', 'titles': title, 
        'rvprop': 'content', 'formatversion': 2, 'format': 'json'
    }
    result = call_api(session, query_data)
    pages = result.get('query', {}).get('pages', [])
    if pages and 'revisions' in pages[0]:
        return pages[0]['revisions'][0]['content']
    return ""

def edit_page_replace(session, title, new_content, token, summary="Bot update"):
    """替换整个页面的内容"""
    print(f"[Fandom Bot] -> 正在提交编辑到页面 '{title}'...")
    edit_data = {
        'action': 'edit', 'title': title, 'text': new_content, 
        'token': token, 'summary': summary, 'bot': True, 'format': 'json'
    }
    
    try:
        edit_result = call_api(session, edit_data)
    except requests.exceptions.RequestException as e:
        print(f"[Fandom Bot] -> ❌ API 网络请求失败: {e}")
        return False 

    if edit_result.get('edit', {}).get('result') == 'Success':
        print("[Fandom Bot] -> 编辑成功。")
        return True
    else:
        # 检查令牌或登录状态错误 (虽然单次运行时会话不会轻易过期，但保留这个检查是好的)
        error_code = edit_result.get('error', {}).get('code')
        if error_code in ['badtoken', 'notloggedin']:
            print(f"[Fandom Bot] -> ❌ 编辑失败：{error_code}。")
            # 在单次运行的 Action 中，如果编辑失败，直接退出让 Actions 重新尝试
            return False 
        
        print(f"[Fandom Bot] -> ❌ 编辑失败。{json.dumps(edit_result, indent=2)}")
        return False

# ======================================================================
#                            【主任务函数 (单次运行)】
# ======================================================================

def run_main_task():
    """GitHub Actions 单次运行的主入口点。"""
    
    with requests.Session() as session:
        # 1. 登录 Fandom
        if not perform_login(session):
            return

        try:
            # 2. 获取编辑令牌
            token = get_csrf_token(session)

            # 3. 获取页面内容
            current_content = get_page_content(session, CHAT_PAGE_TITLE) or ""
            
            # 4. 提取用户评论
            # 使用非贪婪匹配找到第一个 <start>...<end> 块
            match = re.search(r'<start>(.*?)<end>', current_content, re.DOTALL | re.IGNORECASE)

            if match:
                user_comment = match.group(1).strip()
                if not user_comment:
                    print("[Main Task] -> 找到标签，但内容为空。任务结束。")
                    return

                print(f"[Main Task] -> 提取到用户输入:\n-----\n{user_comment}\n-----")

                # 5. 调用 AI 服务获取回复
                ai_reply_text = get_ai_reply(user_comment)

                if ai_reply_text and not ai_reply_text.startswith("❌"):
                    # 6. 格式化并发布回复
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
                    fandom_reply = f"\n* 在 {timestamp}，暗竹回复：{ai_reply_text}\n"
                    
                    full_match_text = match.group(0) # 原始包含标签的文本
                    
                    # 构建替换后的新内容 (将标签和内容替换为用户评论 + 机器人回复)
                    new_content_with_reply = current_content.replace(
                        full_match_text, 
                        f"{user_comment}\n{fandom_reply}", 
                        1 # 只替换第一次出现的
                    )
                    
                    if edit_page_replace(session, CHAT_PAGE_TITLE, new_content_with_reply, token, "Bot automatic reply: removed tags"):
                        print("【主任务】-> ✅ 任务成功完成：已发布回复。")
                        return
                    else:
                        print("【主任务】-> ❌ 编辑失败，终止程序。")
                        # 如果编辑失败，让程序以非零代码退出，Action 会显示失败
                        raise Exception("编辑失败，检查日志")

                else:
                    print(f"[Main Task] -> AI 未生成有效回复。{ai_reply_text}")
                    return

            else:
                print("[Main Task] -> 页面无 <start>...<end> 标记。本次任务结束。")
                return
        
        except Exception as e:
            print(f"\n【主任务】-> 程序发生致命错误: {e}")
            raise e # 让 Actions 失败

if __name__ == "__main__":
    # 确保 requests 库已安装 (requirements.txt 已处理)
    try:
        run_main_task()
    except Exception as e:
        # 捕获异常，并以错误代码退出，确保 Actions 显示失败
        print(f"\n致命错误捕获，程序退出。")
        exit(1) # 以非零状态码退出，让 GitHub Action 标记为失败
