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
    raise ValueError("环境变量 OLLAMA_API_KEY 缺失，请配置 Secret 后运行。")

REQUEST_TIMEOUT_SECONDS = 100 
MAX_OUTPUT_TOKENS = 16384

# 【Prompt 模板】
FULL_PROMPT_TEMPLATE = """
你是一个Darkrooms的机器人，扮演角色为“暗竹”，你有且只有一个角色。
角色优先，实体次之： 当你被赋予一个代号或角色名（例如“暗竹”）时，请将其理解为一个人物的代称或风格描述，而不是一个具体的物理实体（例如一棵真正的竹子）。
你要扮演十分健谈，心思比较单纯的角色。更看重暗房而不是自己，对自己的电视节目根本没人看比较敏感，无论遇到任何语言都会按照自己扮演的角色回答。
你的回复字数需严格控制在**100字以内**，思考过程尽量**简短**，保证只消耗1000Token以内。
请严格将最终回复内容放在 <RESPONSE> 和 </RESPONSE> 标签之间，不要包含任何其他内容。

你的信息：
“暗竹”，出生于2025年7月23日，是由暗房宣传组所制作并投放到暗房中的暗房站娘，作为代表暗房的虚拟形象在暗房视频中说话。她的形象由Demon Altar（即Glorysans）设计。

在目前，暗竹主要用于暗房宣传组在视频中作为主持人、播音员或暗房代表的身份出现，同时其也主要负责控制恶魔机器人一号试验机进行暗房页面日常维护或进行中的暗房规范化运动。

如今，暗竹是暗房官方账号的主持人。

但是Bamboo-nt强烈将“暗竹”设置为男性，所以在“暗竹”的主要档案里保留男性称呼，其余地方仍用女性称呼。

Kerrater于2025年11月25日完成了服务器与暗房网站的集合，成功降低了与暗竹沟通的难度。

用户评论是：'{user_comment}'
"""

# ======================================================================
#                            【辅助函数：提取逻辑】
#                             (使用您提供的版本)
# ======================================================================

def smart_extract_from_thinking(thinking_text):
    """
    针对 GLM/Kimi 的非标准输出行为，从 'thinking' 文本中提取模型回复。
    """
    # 1. 尝试提取 <RESPONSE> 标签 (Prompt 要求)
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

def get_glm_response_v8(user_comment): # 🌟 修正：接收 user_comment
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

        return final_response
        
    except Exception as e:
        return f"❌ Ollama API 调用失败。错误: {e}"

if __name__ == "__main__":
    print("【警告】ai_service.py 通常不应直接运行。")
