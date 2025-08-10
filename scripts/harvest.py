#!/usr/bin/env python
import argparse, os, json
from datetime import datetime, timedelta, timezone
import requests, yaml
from xml.etree import ElementTree as ET
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
TZ = timezone.utc
NOW = datetime.now(TZ)
CUTOFF = NOW - timedelta(days=30)
HEADERS = {"User-Agent": "psai/1.2"}
def iso_date(s, fallback=None):
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return fallback or NOW
def load_json(path, default):
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else default
def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status(); return r.text
def from_github_releases(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    r = requests.get(url, headers=HEADERS, timeout=30); r.raise_for_status()
    out=[]; js=r.json()
    for rel in js:
        dt = rel.get("published_at") or rel.get("created_at") or NOW.isoformat()
        when = iso_date(dt, NOW)
        out.append({"date": when.strftime("%Y-%m-%d"),"headline": rel.get("name") or rel.get("tag_name") or "Release","link": rel.get("html_url")})
    return out
def from_rss(url):
    root = ET.fromstring(fetch(url)); items=[]
    for it in root.findall("./channel/item"):
        title = it.findtext("title") or "Update"; link = it.findtext("link") or ""; pub  = it.findtext("pubDate") or it.findtext("date") or ""
        when = iso_date(pub, NOW); items.append({"date": when.strftime("%Y-%m-%d"), "headline": title.strip(), "link": link.strip()})
    return items
def from_html(cfg):
    if not BeautifulSoup: return []
    soup = BeautifulSoup(fetch(cfg["url"]), "html.parser"); out=[]
    for art in soup.select(cfg.get("item_selector","article"))[:20]:
        ttl = art.select_one(cfg.get("title_selector","h2, h3")); lnk = art.select_one(cfg.get("link_selector","a")); dte = art.select_one(cfg.get("date_selector","time, .date"))
        title = ttl.get_text(strip=True) if ttl else "Update"; link = (lnk.get("href") if lnk else cfg["url"]) or cfg["url"]
        if link and not link.startswith("http"): link = cfg["url"]
        date = (dte.get("datetime") if dte else "") or NOW.strftime("%Y-%m-%d"); when = iso_date(date, NOW)
        out.append({"date": when.strftime("%Y-%m-%d"), "headline": title, "link": link})
    return out
def classify_severity(text):
    t = (text or "").lower()
    if any(k in t for k in ["cve","vulnerability","security","rce","xss","patch"]): return "Security"
    if any(k in t for k in ["major","breaking","incident","outage","downtime","elevated errors","regression","launch","ga","v1.","v2.","released"]): return "Major"
    return "Minor"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sources", required=True); ap.add_argument("--tracker", required=True); ap.add_argument("--log", required=True); args = ap.parse_args()
    cfg = yaml.safe_load(open(args.sources,"r",encoding="utf-8")); log = load_json(args.log, {"items":[]}); existing = {(it.get("date"), it.get("tool"), it.get("headline")) for it in log.get("items",[])}
    for item in cfg.get("items",[]):
        tool = item["tool"]; moniker = item.get("moniker", tool.lower()); category = item.get("category","Updates"); updates=[]
        for src in item.get("sources",[]):
            try:
                typ = src.get("type")
                if typ == "rss": updates += from_rss(src["url"])
                elif typ == "github_releases": updates += from_github_releases(src["repo"])
                elif typ == "html": updates += from_html(src)
            except Exception: continue
        updates = [u for u in updates if iso_date(u["date"], NOW) >= CUTOFF]
        for u in updates:
            key = (u["date"], tool, u["headline"])
            if key in existing: continue
            log["items"].append({"date": u["date"],"tool": tool,"moniker": moniker,"category": category,"severity": classify_severity(u["headline"]),"headline": u["headline"],"impact": "Update detected","link": u.get("link",""),"source": src.get("url") or src.get("repo",""),"notes": ""})
    log["items"].sort(key=lambda x: (x["date"], x["tool"]), reverse=True)
    cutoff = (CUTOFF.date().isoformat()); log["items"] = [it for it in log["items"] if it.get("date","") >= cutoff]
    save_json(args.log, log)
if __name__=="__main__": main()