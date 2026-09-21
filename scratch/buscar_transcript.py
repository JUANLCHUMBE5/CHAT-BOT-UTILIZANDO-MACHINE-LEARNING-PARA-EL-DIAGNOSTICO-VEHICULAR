import json

p = r'C:\Users\leonc\.gemini\antigravity-ide\brain\fdd8aba2-e8cb-4ee6-9ac2-1677e11162f0\.system_generated\logs\transcript_full.jsonl'
with open(p, 'r', encoding='utf-8') as f:
    for line_idx, line in enumerate(f):
        if 'Top 10 Clases con Mayor Ganancia' in line:
            data = json.loads(line)
            content = data.get('content', '')
            step = data.get('step_index')
            source = data.get('source')
            msg_type = data.get('type')
            print(f"Match at line {line_idx}, step {step}, source {source}, type {msg_type}:")
            idx = content.find('Top 10 Clases con Mayor Ganancia')
            print(content[idx:idx+800])
            print("="*60)
