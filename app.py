from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- 1. 配置限流器逻辑 ---
def get_rate_limit_key():
    """
    限流策略：
    - 如果请求里带了 token，就按 token 限制（防止付费用户共享账号）。
    - 如果没带 token，就按 IP 地址限制（防止脚本刷接口）。
    """
    try:
        # 尝试获取 JSON 数据
        data = request.get_json(silent=True)
        if data and 'token' in data:
            return data['token'] 
    except:
        pass
    # 默认按 IP 限制
    return get_remote_address()

# 初始化 Limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    app=app,
    storage_uri="memory://" 
)

# --- 2. 配置 OpenAI ---
api_key = os.environ.get("OPENAI_API_KEY") 
client = OpenAI(api_key=api_key)

# --- 3. 定义 Prompt  ---
PROMPT_TEMPLATE = """
You are a strict exam content creator for the University of Queensland (UQ) Bridging English Program.
Generate a JSON object with **8 distinct reading items**.

### 1. SOURCE MATERIAL SIMULATION (Crucial):
Do NOT write like a generic AI assistant. Write like a journalist for **"The Conversation"** or **"New Scientist"**.
- **Tone**: Academic but engaging, objective, analytical.
- **Vocabulary**: Use precise, less common academic collocations (e.g., "precipitate a crisis", "inherent contradiction", "empirical evidence suggests").
- **Avoid AI Clichés**: Do NOT use phrases like "In conclusion", "It is important to note", "In recent years", "delve into".

### 2. STRUCTURAL REQUIREMENTS (The UQ Pattern):
Each paragraph (120-140 words) MUST follow one of these logical flows strictly:
- **Pattern A (The Twist)**: Start with a commonly held belief or a traditional method -> Introduce a "But" or "However" -> Present new evidence that contradicts the start.
- **Pattern B (The Problem-Solution)**: Describe a complex problem -> Dismiss a simple solution -> Propose a nuanced/scientific solution.
- **Pattern C (The Definition)**: Define a concept broadly -> Narrow it down -> Argue why this specific definition matters.

### 3. QUESTION TYPES (Randomized):
- "What point is the writer making?" (Focus on the argument AFTER the 'However').
- "What is the writer doing in this passage?" (e.g., "Challenging a widespread assumption", "Outlining a causal relationship").
- "Which heading best suits this paragraph?"

### 4. RANDOMIZATION:
- **SHUFFLE ANSWERS**: The correct answer index (0-3) MUST be random.
- **TOPICS**: Mix Biology, Linguistics, Urban Design, Cognitive Science, History.

### 5. OUTPUT:
Return ONLY valid JSON.
{
  "exam_set": [
    {
      "passage": "...",
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct": 2
    },
    ...
  ]
}
"""

# --- 4. 路由定义 (修正部分) ---
# 注意：只保留 POST 方法，且放在最上面
@app.route('/generate-exam', methods=['POST']) 
@limiter.limit("2 per minute")  # 这里的限制规则可以根据需要调整
@limiter.limit("50 per day")
def generate_exam():
    try:
        # 这里直接调用 AI 生成题目
        # (如果你以后要做付费验证，可以在这里加 token 检查逻辑)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": PROMPT_TEMPLATE}],
            response_format={ "type": "json_object" },
            temperature=0.7 
        )
        content = response.choices[0].message.content
        return content 
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- 5. 错误处理 (当被限流时返回友好的提示) ---
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "请求过于频繁，请稍后再试 (Rate limit exceeded)",
        "detail": str(e.description)
    }), 429

if __name__ == '__main__':
    # 注意：Start Command 还是要用 gunicorn -b 0.0.0.0:10000 app:app
    app.run(port=5000, debug=True)