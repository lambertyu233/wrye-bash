import os, sys, re
from bs4 import BeautifulSoup

DOCS = r"D:/code/Skyrim/wrye-bash/Mopy/Docs"
files = [
    "Wrye Bash General Readme.html",
    "Wrye Bash Advanced Readme.html",
    "Wrye Bash Technical Readme.html",
    "Wrye Bash Version History.html",
    "Bash Readme Template.txt",
]

# Elements whose text we skip (scripts/styles/head metadata)
SKIP_TAGS = {"script", "style", "noscript", "meta", "link", "head"}

def count_html_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")
    for t in soup(SKIP_TAGS):
        t.extract()
    texts = []
    for s in soup.stripped_strings:
        s = s.strip()
        if s:
            texts.append(s)
    joined = "\n".join(texts)
    return joined

def count_txt_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()

print("=== Text workload per file ===")
total = 0
for fn in files:
    p = os.path.join(DOCS, fn)
    if not os.path.exists(p):
        print(f"{fn}: MISSING"); continue
    if fn.endswith(".txt"):
        content = count_txt_text(p)
        # rough: count non-whitespace chars
        chars = len(re.sub(r"\s+", "", content))
    else:
        content = count_html_text(p)
        chars = len(content)
    words = len(content.split())
    total += chars
    print(f"{fn}: chars={chars}  words~={words}  bytes={os.path.getsize(p)}")
print(f"TOTAL chars (approx): {total}")

# Test translation endpoint
print("\n=== Translation endpoint test ===")
try:
    from deep_translator import GoogleTranslator
    r = GoogleTranslator(source="en", target="zh-CN").translate("Wrye Bash is a mod management utility for Bethesda games.")
    print("GoogleTranslator OK ->", r)
except Exception as e:
    print("GoogleTranslator FAIL:", repr(e))
