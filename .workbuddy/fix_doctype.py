import os, re
DOCS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Mopy", "Docs"))
files = [
    "Wrye Bash General Readme.zh-CN.html",
    "Wrye Bash Advanced Readme.zh-CN.html",
    "Wrye Bash Technical Readme.zh-CN.html",
    "Wrye Bash Version History.zh-CN.html",
]
for fn in files:
    p = os.path.join(DOCS, fn)
    t = open(p, encoding="utf-8").read()
    orig = t
    t = re.sub(r"^html(?=<html)", "", t, flags=re.S)   # strip stray leading token
    if not t.lstrip().lower().startswith("<!doctype"):
        t = "<!DOCTYPE html>\n" + t
    if t != orig:
        open(p, "w", encoding="utf-8").write(t)
        print("fixed", fn)
    else:
        print("ok (no change)", fn)
