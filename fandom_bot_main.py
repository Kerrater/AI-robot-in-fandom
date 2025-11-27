import os
import time
import re
from datetime import datetime, timedelta, timezone

# 确保 ai_service.py 在同一目录下
from ai_service import get_glm_response_v8 as get_ai_reply

# ======================================================================
#                            【Fandom 配置项】
#                             (从环境变量中读取)
# ======================================================================

# ❗ 安全获取：从 GitHub Actions 的 ENV 中读取用户名和密码
BOT_USERNAME = os.environ.get('FANDOM_BOT_USERNAME') 
BOT_PASSWORD = os.environ.get('FANDOM_BOT_PASSWORD') 

# Fandom Wiki 的域名和页面标题
WIKI_DOMAIN = 'darkrooms.fandom.com/zh' 
CHAT_PAGE_TITLE = '暗竹聊天（测试）' 

API_URL = f'https://{WIKI_DOMAIN}/api.php'

if not all([BOT_USERNAME, BOT_PASSWORD]):
    raise ValueError("Fandom 机器人用户名或密码缺失，请检查 GitHub Secrets 和 YAML 配置。")

# ======================================================================
#                            【Fandom 辅助函数】
#                             (此处省略，假定已存在)
# ======================================================================
# ❗ 您的实际 Fandom 登录和编辑逻辑 (例如：login, get_last_comment, post_reply)
# ❗ 必须放在这里，且不能包含 while True 循环。
# ❗ 确保您已将本地代码中所有 while True 和 time.sleep(300) 移除！


# ======================================================================
#                            【主任务函数】
# ======================================================================

def run_main_task():
    """GitHub Actions 单次运行的主入口点。"""
    
    # 1. 登录 Fandom (使用从 ENV 中读取的用户名和密码)
    print("【主任务】-> 尝试登录 Fandom...")
    # ❗ 假设 login 函数会使用 BOT_USERNAME 和 BOT_PASSWORD
    # session = login(BOT_USERNAME, BOT_PASSWORD, WIKI_DOMAIN)
    # if not session:
    #     print("❌ 登录失败，终止任务。")
    #     return
    
    # 2. 检查最新评论
    print("【主任务】-> 检查聊天室最新评论...")
    # latest_comment = get_last_comment(session, CHAT_PAGE_TITLE)
    
    # ❗ 假设您的逻辑判断是否有新评论，这里使用硬编码模拟流程：
    user_comment = "暗竹，你今天怎么样了？" # 假设这是获取到的新评论内容
    
    if user_comment: # 假设有新评论
        # 3. 调用 AI 服务获取回复 (只传递 user_comment)
        print(f"【主任务】-> 发现新评论：'{user_comment}'，调用 AI 服务...")
        ai_reply_text = get_ai_reply(user_comment) 
        
        print(f"【主任务】-> AI 回复结果: {ai_reply_text}")

        if not ai_reply_text.startswith("❌"):
            # 4. 发布回复
            # post_reply(session, CHAT_PAGE_TITLE, ai_reply_text)
            print("【主任务】-> ✅ 任务成功完成：已准备好发布回复 (代码中已注释发布步骤)")
        else:
            print(f"【主任务】-> ❌ AI 生成回复失败，不发布。")
            
    else:
        print("【主任务】-> 未发现新评论，本次任务结束。")
        

if __name__ == "__main__":
    print(f"==================================================")
    print(f"🤖 Fandom Bot (GitHub Actions 单次运行) 启动...")
    print(f"==================================================")
    run_main_task()
