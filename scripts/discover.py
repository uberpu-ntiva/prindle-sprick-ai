#!/usr/bin/env python
import os, re, json, time, requests
OUT = "data/candidates.json"
def gh_search(deep=False):
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    hdr = {"Accept":"application/vnd.github+json","User-Agent":"psai-discover/1.2"}
    if token: hdr["Authorization"] = f"Bearer {token}"
    days = 30 if deep else 14; per_page = 100 if deep else 30
    q = " ".join(["topic:ai-coding","topic:agentic","topic:mcp","topic:developer-tools","topic:llm-agent","topic:autonomous-ai",f"pushed:>={time.strftime('%Y-%m-%d', time.gmtime(time.time()-days*86400))}"])
    try:
        r = requests.get("https://api.github.com/search/repositories", params={"q":q,"sort":"stars","order":"desc","per_page":per_page}, headers=hdr, timeout=30); r.raise_for_status(); js = r.json()
        for it in js.get("items", []):
            yield {"tool": it["name"],"moniker": re.sub(r"[^a-z0-9]+","-", it["name"].lower()).strip("-"),"category": "OSS","source_type": "OSS","repo_url": it["html_url"],"website_url": it.get("homepage") or "","feed_url": it["html_url"].rstrip("/") + "/releases.atom"}
    except Exception: return
def rss_stub(tool, moniker, site, feed, category="Discovery", source_type="Press"):
    return {"tool": tool, "moniker": moniker, "category": category, "source_type": source_type,"repo_url":"", "website_url": site, "feed_url": feed}
def candidates():
    deep = os.getenv("PSAI_DEEP","0") == "1"
    for c in gh_search(deep=deep): yield c
    core=[("Product Hunt — Dev/AI","ph-dev-ai","https://www.producthunt.com","https://www.producthunt.com/feed"),("Hacker News — Show","hn-show","https://news.ycombinator.com/show","https://hnrss.org/show"),("Reddit r/Programming","reddit-programming","https://www.reddit.com/r/Programming/","https://www.reddit.com/r/Programming/.rss"),("Reddit r/LocalLLaMA","reddit-localllama","https://www.reddit.com/r/LocalLLaMA/","https://www.reddit.com/r/LocalLLaMA/.rss"),("Reddit r/MachineLearning","reddit-ml","https://www.reddit.com/r/MachineLearning/","https://www.reddit.com/r/MachineLearning/.rss"),("TechCrunch AI","tc-ai","https://techcrunch.com/tag/ai/","https://techcrunch.com/tag/ai/feed/"),("The Verge AI","verge-ai","https://www.theverge.com/ai-artificial-intelligence","https://www.theverge.com/rss/index.xml"),("VentureBeat AI","vb-ai","https://venturebeat.com/category/ai/","https://venturebeat.com/feed/"),("Ars Technica AI","ars-ai","https://arstechnica.com/information-technology/","https://feeds.arstechnica.com/arstechnica/technology-lab"),("MIT Tech Review AI","mittr-ai","https://www.technologyreview.com/ai/","https://www.technologyreview.com/feed/"),("Ben's Bites","bens-bites","https://www.bensbites.co/","https://www.bensbites.co/feed"),("Latent.Space","latent-space","https://www.latent.space/","https://www.latent.space/feed"),("Hugging Face Spaces (code/dev/agent)","hf-spaces","https://huggingface.co/spaces","https://huggingface.co/blog/feed.xml"),("OpenAI Community","openai-community","https://community.openai.com/","https://community.openai.com/latest.rss"),("Anthropic Community","anthropic-community","https://community.anthropic.com/","https://community.anthropic.com/latest.rss"),("Google AI Blog","google-ai-blog","https://ai.googleblog.com/","https://ai.googleblog.com/feeds/posts/default"),("npm ai/dev search","npm-ai","https://www.npmjs.com/search?q=keywords:ai%20developer","https://www.npmjs.com/~rss"),("PyPI ai/dev search","pypi-ai","https://pypi.org/search/?q=ai+developer","https://pypi.org/rss/updates.xml"),("Docker Hub ai/dev","docker-ai","https://hub.docker.com/search?q=agent%20devtools&type=image",""),("Papers With Code","pwc","https://paperswithcode.com/","https://paperswithcode.com/feeds/latest"),("arXiv cs.AI/cs.SE","arxiv-ai-se","https://arxiv.org/","https://export.arxiv.org/rss/cs.AI")]
    for n,m,s,f in core: yield rss_stub(n,m,s,f)
    if deep:
        for n,m,s,f in [("Reddit r/Artificial","reddit-artificial","https://www.reddit.com/r/Artificial/","https://www.reddit.com/r/Artificial/.rss"),("Reddit r/AGI","reddit-agi","https://www.reddit.com/r/AGI/","https://www.reddit.com/r/AGI/.rss"),("Awesome AI lists","awesome-ai","https://github.com/topics/awesome-ai",""),("Awesome Agents lists","awesome-agents","https://github.com/topics/agents",""),("OSS Insight trending (AI)","oss-insight","https://ossinsight.io/","")]:
            yield rss_stub(n,m,s,f)
def main():
    out = list(candidates()); os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f: json.dump({"items": out}, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT} with {len(out)} entries (deep={os.getenv('PSAI_DEEP','0')}).")
if __name__ == "__main__": main()
