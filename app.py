from flask import Flask, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- 配置区 ---
# 请替换为你的实际 API Key
api_key = os.environ.get("OPENAI_API_KEY") 
client = OpenAI(api_key=api_key)
# 修改 Prompt，要求生成8道题的列表
# app.py

PROMPT_TEMPLATE = """
You are an expert exam writer for the University of Queensland (UQ) Bridging English Program (BEP). 
Generate a JSON object containing **8 distinct reading questions** simulating "Stage 1 Reading".

### 1. Passage Guidelines (Strict):
- **Length**: 110-140 words per paragraph.
- **Style**: Academic but accessible (IELTS 6.0-6.5 level). 
- **Structure**: almost all paragraphs should employ a **"Contrast" or "Misconception vs. Reality" structure**. 
    - *Example*: "People often think X... However, recent research suggests Y..."
- **Topics**: Varied academic topics (Biology, Urban Planning, Psychology, Tech, History).

### 2. Question Guidelines (Rotate strictly between these 3 types):
Type A: **"What point is the writer making...?"** (Main Idea)
Type B: **"What is the writer doing...?"** (Function, e.g., "Correcting a misunderstanding", "Outlining a process")
Type C: **"What would make a good heading...?"**

### 3. CRITICAL INSTRUCTION - RANDOMIZE ANSWERS:
- **SHUFFLE THE OPTIONS**: The correct answer MUST NOT always be option A. 
- **Random Distribution**: Across the 8 questions, ensure the correct index (0, 1, 2, 3) is varied. roughly 25% A, 25% B, 25% C, 25% D.
- **Do NOT** output 0 for every question.

### 4. Output Format:
Return ONLY valid JSON.
{
  "exam_set": [
    {
      "passage": "Text...",
      "question": "Question text...",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct": 2  // INTEGER (0=A, 1=B, 2=C, 3=D). CHANGE THIS RANDOMLY!
    },
    ... (repeat 8 times)
  ]
}
"""
@app.route('/generate-exam', methods=['GET'])
def generate_exam():
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": PROMPT_TEMPLATE}],
            response_format={ "type": "json_object" },
            temperature=0.7 # 增加一点随机性以获得多样化的话题
        )
        content = response.choices[0].message.content
        return content # 直接返回 JSON 字符串
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)