#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translate the Wrye Bash docs (Mopy/Docs) from English to Simplified Chinese,
preserving HTML structure, links, images and the wtxt markup of the .txt template.

Backends (set BACKEND + KEY below):
  - "mymemory" : free, no key  (daily quota ~5000 words/IP)
  - "google"   : free via deep_translator (may be rate-limited)
  - "deepl"    : DeepL API, needs DEEPL_KEY
  - "openai"   : OpenAI / DeepSeek / any OpenAI-compatible chat API
                 needs OPENAI_KEY (+ optional OPENAI_BASE_URL, OPENAI_MODEL)

Usage:
  python translate_docs.py                 # translate everything
  python translate_docs.py --sample 1200  # only first ~N words of each HTML doc
"""
import os, re, sys, time, json, argparse
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.normpath(os.path.join(HERE, "..", "Mopy", "Docs"))

# ----------------------------- config --------------------------------------
BACKEND = os.environ.get("BACKEND", "mymemory")   # dummy|mymemory|google|deepl|local
DEEPL_KEY = os.environ.get("DEEPL_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MYMEMORY_EMAIL = os.environ.get("MYMEMORY_EMAIL", "")   # raises free quota
LOCAL_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://10.168.1.146:1234/v1")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "hy-mt2-7b@q8_0")
LOCAL_KEY = os.environ.get("LOCAL_KEY", "lm-studio")
SLEEP = 0.05                  # delay between calls (local model is fast)
BATCH = 24                    # segments per chat/DeepL batch
# ---------------------------------------------------------------------------

SKIP_TAGS = {"script", "style", "noscript"}
CODE_TAGS = {"code", "pre", "kbd", "samp", "var"}   # keep code untranslated

FILES = [
    "Wrye Bash General Readme.html",
    "Wrye Bash Advanced Readme.html",
    "Wrye Bash Technical Readme.html",
    "Wrye Bash Version History.html",
]

# ---------------------------------------------------------------------------
# Translation backends
# ---------------------------------------------------------------------------
class Translator:
    def translate(self, texts):  # list[str] -> list[str]
        raise NotImplementedError

class DummyTranslator(Translator):
    """Pass-through: returns text unchanged. Useful to validate that the
    pipeline preserves HTML structure without spending any API quota."""
    def translate(self, texts):
        return list(texts)

class MyMemoryTranslator(Translator):
    def __init__(self):
        from deep_translator import MyMemoryTranslator as MM
        self.MM = MM
    def translate(self, texts):
        out = []
        for t in texts:
            if not t.strip():
                out.append(t); continue
            try:
                r = self.MM(source="english", target="chinese simplified",
                            email=MYMEMORY_EMAIL or None).translate(t)
                if not r:
                    r = t
            except Exception as e:
                sys.stderr.write(f"[mymemory] {e}\n"); r = t
            out.append(r)
            time.sleep(SLEEP)
        return out

class GoogleTranslator(Translator):
    def __init__(self):
        from deep_translator import GoogleTranslator as GT
        self.GT = GT
    def translate(self, texts):
        out = []
        for t in texts:
            if not t.strip():
                out.append(t); continue
            try:
                r = self.GT(source="en", target="zh-CN").translate(t)
                if not r: r = t
            except Exception as e:
                sys.stderr.write(f"[google] {e}\n"); r = t
            out.append(r)
            time.sleep(SLEEP)
        return out

class DeepLTranslator(Translator):
    def __init__(self, key):
        import requests
        self.key = key; self.requests = requests
    def translate(self, texts):
        texts = [t for t in texts]
        out = []
        for i in range(0, len(texts), BATCH):
            chunk = texts[i:i+BATCH]
            try:
                r = self.requests.post("https://api-free.deepl.com/v2/translate",
                    data={"target_lang": "ZH", "source_lang": "EN",
                          "text": chunk},
                    headers={"Authorization": f"DeepL-Auth-Key {self.key}"}, timeout=30)
                res = r.json()
                tr = [x["text"] for x in res["translations"]]
                out.extend(tr)
            except Exception as e:
                sys.stderr.write(f"[deepl] {e}\n"); out.extend(chunk)
            time.sleep(SLEEP)
        return out

class LocalTranslator(Translator):
    """OpenAI-compatible local LLM (e.g. LM Studio) used as a translator.
    Sends one segment per request concurrently (reliable, no batching fragility)."""
    def __init__(self, base_url, model, api_key, workers=8):
        import requests
        self.requests = requests
        self.base = base_url.rstrip("/")
        self.model = model
        self.headers = {"Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"}
        self.workers = workers
        self.sys = ("You are a professional English-to-Simplified-Chinese translator for "
                   "Bethesda game modding documentation (Wrye Bash). Keep proper nouns like "
                   "Wrye Bash, BAIN, Bashed Patch, Oblivion, Skyrim, ESP/ESL/ESM unchanged. "
                   "Do not add any explanation.")

    def _post(self, content, max_tokens):
        data = {"model": self.model,
                "messages": [{"role": "system", "content": self.sys},
                             {"role": "user", "content": content}],
                "temperature": 0.2, "max_tokens": max_tokens}
        for attempt in range(3):
            try:
                r = self.requests.post(f"{self.base}/chat/completions",
                                       headers=self.headers, json=data, timeout=300)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                sys.stderr.write(f"[local] attempt {attempt+1} failed: {e}\n")
                time.sleep(2 * (attempt + 1))
        return None

    def _one(self, text):
        if not text.strip():
            return text
        ans = self._post("Translate the following English text into Simplified Chinese. "
                         "Output only the translation.\n\n" + text, 4096)
        return ans.strip() if ans is not None else text

    def translate(self, texts):
        from concurrent.futures import ThreadPoolExecutor
        out = [None] * len(texts)
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(self._one, t): i for i, t in enumerate(texts)}
            done = 0
            for fut in futs:
                i = futs[fut]
                try:
                    out[i] = fut.result()
                except Exception:
                    out[i] = texts[i]
                done += 1
                if done % 200 == 0:
                    sys.stderr.write(f"[local] {done}/{len(texts)} done\n")
        return out

def get_translator():
    if BACKEND == "dummy":
        return DummyTranslator()
    if BACKEND == "mymemory":
        return MyMemoryTranslator()
    if BACKEND == "google":
        return GoogleTranslator()
    if BACKEND == "deepl":
        if not DEEPL_KEY:
            raise SystemExit("DEEPL_KEY not set")
        return DeepLTranslator(DEEPL_KEY)
    if BACKEND == "openai":
        if not OPENAI_KEY:
            raise SystemExit("OPENAI_KEY not set")
        return ChatTranslator(OPENAI_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
    if BACKEND == "local":
        return LocalTranslator(LOCAL_BASE_URL, LOCAL_MODEL, LOCAL_KEY)
    raise SystemExit(f"Unknown BACKEND={BACKEND}")

# ---------------------------------------------------------------------------
# HTML translation
# ---------------------------------------------------------------------------
def is_translatable(string_node):
    s = str(string_node)
    if not s.strip():
        return False
    parent = string_node.parent
    if parent is None:
        return False
    if parent.name in SKIP_TAGS:
        return False
    # walk ancestors for translate=no or code tags
    for anc in parent.parents:
        if anc.get("translate") == "no":
            return False
        if anc.name in CODE_TAGS:
            return False
    if parent.name in CODE_TAGS:
        return False
    # skip pure numbers / punctuation / very short non-words
    if re.fullmatch(r"[\s\W\d_]+", s):
        return False
    return True

def translate_html(path, translator, sample_words=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    # title
    if soup.title and soup.title.string and soup.title.string.strip():
        soup.title.string.replace_with(
            translator.translate([soup.title.string.strip()])[0])

    nodes = [n for n in soup.find_all(string=True) if is_translatable(n)]
    # optional sample truncation by word count
    if sample_words is not None:
        acc = 0; kept = []
        for n in nodes:
            w = len(n.split())
            if acc >= sample_words:
                break
            kept.append(n); acc += w
        nodes = kept

    originals = [str(n).strip() for n in nodes]
    # re-strip empties mapping
    idx_map = [(n, o) for n, o in zip(nodes, originals) if o]
    batch_in = [o for _, o in idx_map]
    translated = translator.translate(batch_in)
    for (n, _), t in zip(idx_map, translated):
        n.replace_with(t)

    # lang attr
    if soup.html:
        soup.html["lang"] = "zh-CN"

    out = str(soup)
    # bs4+lxml drops the doctype and may emit a stray leading "html" token;
    # restore a clean <!DOCTYPE html> and remove that stray token.
    out = re.sub(r"^html(?=<html)", "", out, flags=re.S)
    if not out.lstrip().lower().startswith("<!doctype"):
        out = "<!DOCTYPE html>\n" + out
    return out

# ---------------------------------------------------------------------------
# TXT (wtxt) translation  -- preserve == headers ==, [[links]], {{tags}}, <code>
# ---------------------------------------------------------------------------
MARKUP_RE = re.compile(r"(==+.*?==+|<code>.*?</code>|\[\[.*?\]\]|{{.*?}}|<\w+.*?>|</\w+>)", re.S)

def translate_txt(path, translator, sample_words=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    out = []
    acc = 0
    for line in lines:
        if sample_words is not None and acc >= sample_words:
            out.append(line); continue
        if not line.strip():
            out.append(line); continue
        # protect markup, translate the rest
        parts = MARKUP_RE.split(line)
        newparts = []
        for p in parts:
            if not p:
                continue
            if MARKUP_RE.fullmatch(p):
                newparts.append(p)   # keep markup verbatim
            else:
                t = p.strip()
                if t:
                    tr = translator.translate([t])[0]
                    # preserve leading/trailing spaces
                    lead = p[:len(p)-len(p.lstrip())]
                    trail = p[len(p.rstrip()):]
                    newparts.append(lead + tr + trail)
                else:
                    newparts.append(p)
        out.append("".join(newparts))
        acc += len(line.split())
    return "\n".join(out)

# ---------------------------------------------------------------------------
def write_zh(path, content):
    base, ext = os.path.splitext(path)
    out = base + ".zh-CN" + ext
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None,
                    help="translate only first N words per HTML doc (demo)")
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to given filenames")
    ap.add_argument("--backend", default=None,
                    help="override BACKEND: dummy|mymemory|google|deepl|local")
    ap.add_argument("--model", default=None,
                    help="override LOCAL_MODEL (local backend)")
    ap.add_argument("--base-url", default=None,
                    help="override LOCAL_BASE_URL (local backend)")
    args = ap.parse_args()

    global BACKEND, LOCAL_MODEL, LOCAL_BASE_URL
    if args.backend:
        BACKEND = args.backend
    if args.model:
        LOCAL_MODEL = args.model
    if args.base_url:
        LOCAL_BASE_URL = args.base_url
    tr = get_translator()
    print(f"Backend: {BACKEND}")

    targets = FILES
    if args.only:
        targets = [t for t in targets if t in args.only]

    for fn in targets:
        p = os.path.join(DOCS, fn)
        print(f"-> {fn}")
        content = translate_html(p, tr, sample_words=args.sample)
        out = write_zh(p, content)
        print(f"   wrote {os.path.basename(out)}")

    # template txt
    tpl = os.path.join(DOCS, "Bash Readme Template.txt")
    if os.path.exists(tpl) and (args.only is None or "Bash Readme Template.txt" in args.only):
        print("-> Bash Readme Template.txt")
        tcontent = translate_txt(tpl, tr, sample_words=args.sample)
        out = write_zh(tpl, tcontent)
        print(f"   wrote {os.path.basename(out)}")

    print("Done.")

if __name__ == "__main__":
    main()
