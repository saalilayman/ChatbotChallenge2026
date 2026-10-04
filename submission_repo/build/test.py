from pathlib import Path

import requests
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.llm import describe_image

src = "https://innowings.engg.hku.hk/wp-content/uploads/2019/01/kenneth-wong.jpg"
r = requests.get(src, timeout=30)
print(r.status_code, r.headers.get("content-type"), len(r.content), r.content[:8])
# a real JPEG starts with b'\xff\xd8\xff', a PNG with b'\x89PNG'

p = Path("data/_test.jpg"); p.write_bytes(r.content)

print(repr(describe_image(str(p), "Describe this image in one sentence.")))

from openai import AzureOpenAI
from bot.llm import _client, VISION_URL, VISION_DEPLOYMENT
from build.images import DESCRIPTION_PROMPT
import base64

b64 = base64.b64encode(open("data/_test.jpg","rb").read()).decode()
r = _client(VISION_URL).chat.completions.create(
    model=VISION_DEPLOYMENT, max_completion_tokens=800,
    messages=[{"role":"user","content":[
        {"type":"text","text":DESCRIPTION_PROMPT},
        {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
print(r.choices[0].finish_reason, r.usage)