import os
import json
import requests
import re

# ======================================================================
#                             【AI 配置项】
#                             (从环境变量中读取)
# ======================================================================

OLLAMA_API_BASE = os.environ.get('OLLAMA_API_BASE', "https://ollama.com/api") 
OLLAMA_API_KEY = os.environ.get('OLLAMA_API_KEY') 
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', "kimi-k2:1t-cloud") 

if not OLLAMA_API_KEY:
    raise ValueError("环境变量 OLLAMA_API_KEY 缺失，请配置 Secret 后运行。")

REQUEST_TIMEOUT_SECONDS = 100 
MAX_OUTPUT_TOKENS = 16384

# 【Prompt 模板】 (保持不变)
FULL_PROMPT_TEMPLATE = """
你是一个Darkrooms的机器人... (此处省略，使用您的完整 Prompt 内容)
用户评论是：'{user_comment}'
"""

# ======================================================================
#                            【辅助函数：提取逻辑】
# ======================================================================

def smart_extract_from_thinking(thinking_text):
    """
    针对 GLM/Kimi 的非标准输出行为，从 'thinking' 文本中提取模型回复。
    """
    # 1. 尝试提取 <RESPONSE> 标签 
    match_tag = re.search(r'<RESPONSE>(.*?)</RESPONSE>', thinking_text, re.DOTALL)
    if match_tag:
        return match_tag.group(1).strip()
    
    # 2. 尝试提取 '尝试X' 后的回复 
    match_attempt = re.findall(r'尝试\d+（.*?）：\s*[\'"]?(.+?)[\'"]?\s*$', thinking_text, re.MULTILINE)
    if match_attempt:
        return match_attempt[-1].strip()
        
    # 3. 如果以上都失败，则尝试去除明显的分析/思考前缀
    clean_text = re.sub(r'^(.*?(\s*[\d\.]\s*|\s*[a-zA-Z]+\s*)\s*[:：])', '', thinking_text, count=1, flags=re.MULTILINE).strip()
    
    if len(clean_text) > 20: 
        return clean_text
    
    # 4. 实在不行，返回思考文本的开头作为警告
    return f"【思考失败，无法提取回复】: {thinking_text[:100]}..."

# ======================================================================
#                          【Ollama API 调用 V8：最终修复版】
# ======================================================================

def get_glm_response_v8(user_comment):
    """最终修复版：非流式请求，修复路径和 Prompt 构造，并保证输出无标签。"""
    
    full_prompt = FULL_PROMPT_TEMPLATE.format(user_comment=user_comment) 
    
    print(f"-> 正在连接 Ollama Cloud API: {OLLAMA_API_BASE} (超时: {REQUEST_TIMEOUT_SECONDS}秒, Token限制: {MAX_OUTPUT_TOKENS})...")
    
    headers = {'Authorization': f'Bearer {OLLAMA_API_KEY}', 'Content-Type': 'application/json'}
    
    payload = {
        'model': OLLAMA_MODEL,
        'messages': [{'role': 'user', 'content': full_prompt}],
        'options': {'temperature': 0.7, 'num_predict': MAX_OUTPUT_TOKENS},
        'stream': False
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_API_BASE}/chat",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status() 

        response_json = response.json()
        
        # 提取逻辑
        raw_output = response_json.get('message', {}).get('content', '').strip()
        thinking_output = response_json.get('message', {}).get('thinking', '').strip()
        
        if raw_output:
            final_response = raw_output
        elif thinking_output:
            final_response = smart_extract_from_thinking(thinking_output)
        else:
            final_response = "❌ 无法获取任何内容（content和thinking都为空）。"

        # -----------------------------------------------------
        # 🌟 新增：最终清理步骤，确保移除 <RESPONSE> 标签
        # -----------------------------------------------------
        if final_response and not final_response.startswith("❌"):
            match_tag = re.search(r'<RESPONSE>(.*?)</RESPONSE>', final_response, re.DOTALL | re.IGNORECASE)
            if match_tag:
                # 如果找到标签，则返回标签内的内容
                final_response = match_tag.group(1).strip()
            # 否则，返回原始内容（此时 final_response 可能是 raw_output 或 smart_extract_from_thinking 的结果）
        
        return final_response
        
    except Exception as e:
        return f"❌ Ollama API 调用失败。错误: {e}"

if __name__ == "__main__":
    print("【警告】ai_service.py 通常不应直接运行。")
