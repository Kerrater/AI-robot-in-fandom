import os
import json
import requests
import re

# ======================================================================
#                             【AI 配置项】
#                             (从环境变量中读取)
# ======================================================================

# ❗ 安全获取：从 GitHub Actions 的 ENV 中读取 API 密钥
OLLAMA_API_BASE = os.environ.get('OLLAMA_API_BASE', "https://ollama.com/api") 
OLLAMA_API_KEY = os.environ.get('OLLAMA_API_KEY') 
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', "kimi-k2:1t-cloud") 

if not OLLAMA_API_KEY:
    # 在 GitHub Actions 中，如果密钥未设置，这里会立即报错
    raise ValueError("环境变量 OLLAMA_API_KEY 缺失，请配置 Secret 后运行。")

REQUEST_TIMEOUT_SECONDS = 100 
MAX_OUTPUT_TOKENS = 16384

# 【Prompt 模板保持不变】
FULL_PROMPT_TEMPLATE = """
你是一个Darkrooms的机器人... (此处省略，使用您的完整 Prompt 内容)
用户评论是：'{user_comment}'
"""

# ======================================================================
#                            【辅助函数：提取逻辑】
#                             (保持不变)
# ======================================================================
# ❗ 请确保您的 smart_extract_from_thinking 函数包含在这里。


# ======================================================================
#                          【Ollama API 调用 V8：最终修复版】
# ======================================================================

def get_glm_response_v8(user_comment): # 🌟 修正：只接收 user_comment
    """最终修复版：非流式请求，修复路径和 Prompt 构造。"""
    
    # 🌟 关键：在函数内部构造完整的 Prompt
    full_prompt = FULL_PROMPT_TEMPLATE.format(user_comment=user_comment) 
    
    print(f"-> 正在连接 Ollama Cloud API: {OLLAMA_API_BASE} (超时: {REQUEST_TIMEOUT_SECONDS}秒, Token限制: {MAX_OUTPUT_TOKENS})...")
    
    headers = {'Authorization': f'Bearer {OLLAMA_API_KEY}', 'Content-Type': 'application/json'}
    
    payload = {
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'user', 'content': full_prompt}], # 使用构造好的 full_prompt
        'options': {'temperature': 0.7, 'num_predict': MAX_OUTPUT_TOKENS},
        'stream': False
    }
    
    try:
        # 路径恢复为用户本地可运行的 /chat
        response = requests.post(
            f"{OLLAMA_API_BASE}/chat", # 🌟 修正 API 路径
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status() 

        response_json = response.json()
        
        # ❗ 您的调试和提取逻辑保持不变
        raw_output = response_json.get('message', {}).get('content', '').strip()
        thinking_output = response_json.get('message', {}).get('thinking', '').strip()
        
        # ... (智能提取逻辑)
        if raw_output:
            final_response = raw_output
        elif thinking_output:
            final_response = smart_extract_from_thinking(thinking_output)
        else:
            final_response = "❌ 无法获取任何内容（content和thinking都为空）。"

        return final_response
        
    except Exception as e:
        # 打印详细错误，帮助调试
        return f"❌ Ollama API 调用失败。错误: {e}"

if __name__ == "__main__":
    print("【警告】ai_service.py 通常不应直接运行。")
