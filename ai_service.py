import os
import json
import requests
import time
import re

# ======================================================================
#                             【AI 配置项】
# ======================================================================

# !!! 1. 从环境变量中读取敏感信息 !!!
OLLAMA_API_BASE = os.environ.get('OLLAMA_API_BASE', "https://ollama.com/api") 
OLLAMA_API_KEY = os.environ.get('OLLAMA_API_KEY') 
if not OLLAMA_API_KEY:
    raise ValueError("环境变量 OLLAMA_API_KEY 缺失，请配置后再运行。")
    
# 2. 从您提供的代码中更新模型和 Token 限制
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', "kimi-k2:1t-cloud") 

REQUEST_TIMEOUT_SECONDS = 100 
MAX_OUTPUT_TOKENS = 16384

# 【优化后的 Prompt】(请注意，我已将 {user_comment} 替换为占位符)
FULL_PROMPT_TEMPLATE = """
你是一个Darkrooms的机器人，扮演角色为“暗竹”，你有且只有一个角色。
... (Prompt 内容保持不变) ...
Kerrater于2025年11月25日完成了服务器与暗房网站的集合，成功降低了与暗竹沟通的难度。

用户评论是：'{user_comment}'
"""

# ======================================================================
#                          【辅助函数 (保持不变)】
# ======================================================================
# ... (smart_extract_from_thinking 函数保持不变) ...

def smart_extract_from_thinking(thinking_text):
    """
    针对 GLM-4.6-cloud 的非标准输出行为，从 'thinking' 文本中提取模型构思的回复。
    """
    # 1. 尝试提取 <RESPONSE> 标签 (Prompt 要求)
    match_tag = re.search(r'<RESPONSE>(.*?)</RESPONSE>', thinking_text, re.DOTALL)
    if match_tag:
        return match_tag.group(1).strip()
    
    # 2. 尝试提取 '起草 - 尝试X' 后的第一个回复 (根据之前的观察)
    match_attempt = re.findall(r'尝试\d+（.*?）：\s*[\'"]?(.+?)[\'"]?\s*$', thinking_text, re.MULTILINE)
    
    if match_attempt:
        return f"【智能提取尝试回复】: {match_attempt[-1].strip()}"
    
    # 3. 实在不行，返回思考文本的开头作为警告
    return f"【思考失败，无法提取回复】: {thinking_text[:100]}..."


# ======================================================================
#                      【Ollama API 调用 V8 (重构调用参数)】
# ======================================================================

def get_glm_response_v8(user_comment): # 接收用户评论
    """最终修复版：非流式请求，并使用智能提取逻辑。"""
    
    # 1. 填充完整 Prompt
    full_prompt = FULL_PROMPT_TEMPLATE.format(user_comment=user_comment)
    
    print(f"-> 正在连接 Ollama Cloud API: {OLLAMA_API_BASE} (超时: {REQUEST_TIMEOUT_SECONDS}秒, Token限制: {MAX_OUTPUT_TOKENS})...")
    
    headers = {'Authorization': f'Bearer {OLLAMA_API_KEY}', 'Content-Type': 'application/json'}
    
    payload = {
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'user', 'content': full_prompt}],
        'options': {'temperature': 0.7, 'num_predict': MAX_OUTPUT_TOKENS},
        'stream': False
    }
    
    # ... (try/except 块保持不变) ...
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/chat",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status() 

        response_json = response.json()
        
        # --- 调试信息 ---
        print("--- 原始 API 响应开始 ---")
        # 移除此调试信息，在 GitHub Actions 中避免刷屏
        # print(json.dumps(response_json, indent=2, ensure_ascii=False)) 
        print("--- 原始 API 响应结束 ---")

        # 1. 获取 raw_output
        raw_output = response_json.get('message', {}).get('content', '').strip()
        thinking_output = response_json.get('message', {}).get('thinking', '').strip()
        
        # 2. 智能提取逻辑
        if not raw_output and thinking_output:
            final_response = smart_extract_from_thinking(thinking_output)
        elif raw_output:
            final_response = raw_output
        else:
            final_response = "❌ 无法获取任何内容（content和thinking都为空）。"
            
        return final_response
        
    except requests.exceptions.ReadTimeout:
        return f"❌ Ollama API 调用失败: 请求在 {REQUEST_TIMEOUT_SECONDS} 秒内超时。"
    except Exception as e:
        return f"❌ Ollama API 调用失败。错误: {e}"

# ======================================================================
#                          【主程序入口 (移除测试逻辑)】
# ======================================================================

if __name__ == "__main__":
    # 移除原有的测试逻辑，因为 ai_service 不应该自行进行测试
    print("【警告】ai_service.py 通常不应直接运行。请通过 fandom_bot_main.py 调用。")
    pass