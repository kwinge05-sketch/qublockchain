#!/usr/bin/env python3
"""
Builds the weekly newsletter email from files already in the repo:
  news.json            -> the week's top stories (made by fetch_news.py)
  data/events.json     -> upcoming events (past ones are skipped)
  newsletter/intro.txt -> optional personal note (blank lines separate paragraphs)

Writes newsletter/latest.html (email-ready) and newsletter/latest.txt (plain text).
Standard library only.
"""
import html
import json
import os
import re
import sys
from datetime import date, datetime

ROOT = os.environ.get("NEWSLETTER_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKEDIN = "https://www.linkedin.com/company/blockchainqu/"
CAMPUS = "https://quinnipiac.campusgroups.com/feeds?type=club&type_id=35573&tab=about"
INK, GOLD, PAPER, SOFT = "#12142B", "#D9A62E", "#F1F2EE", "#5B5D6E"


def p(*parts):
    return os.path.join(ROOT, *parts)


def load_json(rel):
    try:
        with open(p(rel), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def esc(text):
    return html.escape(str(text or ""), quote=True)


def https(url):
    url = (url or "").strip()
    return url if re.match(r"^https://[^\s]+$", url) else ""


def parse_day(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def pretty(value):
    d = parse_day(value)
    return f"{d.strftime('%b')} {d.day}" if d else ""


def intro_paragraphs():
    try:
        with open(p("newsletter", "intro.txt"), encoding="utf-8") as f:
            parts = [x.strip() for x in f.read().split("\n\n") if x.strip()]
            if parts:
                return parts
    except Exception:
        pass
    return ["Here are the five biggest blockchain stories this week, plus what's coming up at the club."]


def gather(today):
    news = [n for n in load_json("news.json").get("items", []) if n.get("title") and https(n.get("link"))][:5]
    events = []
    for e in load_json(os.path.join("data", "events.json")).get("events", []):
        if not e.get("title"):
            continue
        d = parse_day(e.get("date"))
        if d and d < today:
            continue
        events.append((d or date.max, e))
    events.sort(key=lambda x: x[0])
    return news, [e for _, e in events][:5]


def build_html(today, intro, news, events):
    def para(t):
        return f'<p style="margin:0 0 14px;font:15px/1.6 Arial,Helvetica,sans-serif;color:{SOFT};">{esc(t)}</p>'

    def heading(t):
        return (f'<tr><td style="padding:30px 32px 6px;font:bold 12px Arial,Helvetica,sans-serif;letter-spacing:1px;'
                f'text-transform:uppercase;color:#8A6A12;">{esc(t)}</td></tr>')

    rows = [f'<tr><td style="padding:28px 32px 0;">{"".join(para(t) for t in intro)}</td></tr>', heading("Top stories this week")]
    if news:
        for n in news:
            when = pretty(n.get("published"))
            meta = esc(n.get("source", "")) + (f" &middot; {when}" if when else "")
            summ = f'<div style="margin-top:6px;font:14px/1.55 Arial,Helvetica,sans-serif;color:{SOFT};">{esc(n.get("summary"))}</div>' if n.get("summary") else ""
            rows.append(
                f'<tr><td style="padding:16px 32px;border-top:1px solid #E4E4DE;">'
                f'<div style="font:12px Arial,Helvetica,sans-serif;color:#8A6A12;">{meta}</div>'
                f'<a href="{esc(https(n["link"]))}" style="font:bold 18px/1.35 Georgia,serif;color:{INK};text-decoration:none;">{esc(n["title"])}</a>'
                f'{summ}</td></tr>')
    else:
        rows.append(f'<tr><td style="padding:10px 32px 16px;">{para("No stories this week. Check back next time.")}</td></tr>')

    if events:
        rows.append(heading("Upcoming events"))
        for e in events:
            where = f' &middot; {esc(e["location"])}' if e.get("location") else ""
            link = https(e.get("link"))
            cta = (f'<div style="margin-top:8px;"><a href="{esc(link)}" style="font:bold 13px Arial,Helvetica,sans-serif;color:#1F7A6E;">'
                   f'{esc(e.get("linkLabel") or "Learn more")} &rarr;</a></div>') if link else ""
            summ = f'<div style="margin-top:4px;font:14px/1.55 Arial,Helvetica,sans-serif;color:{SOFT};">{esc(e.get("summary"))}</div>' if e.get("summary") else ""
            rows.append(
                f'<tr><td style="padding:14px 32px;border-top:1px solid #E4E4DE;">'
                f'<div style="font:12px Arial,Helvetica,sans-serif;color:#8A6A12;">{esc(e.get("dateText") or e.get("date") or "Date to be announced")}{where}</div>'
                f'<div style="font:bold 17px/1.35 Georgia,serif;color:{INK};">{esc(e["title"])}</div>{summ}{cta}</td></tr>')

    def button(label, url, solid):
        style = f"background:{GOLD};color:{INK};" if solid else f"border:1px solid {INK};color:{INK};"
        return (f'<a href="{esc(url)}" style="display:inline-block;margin:0 8px 8px 0;padding:12px 20px;font:bold 14px Arial,Helvetica,sans-serif;'
                f'text-decoration:none;{style}">{esc(label)}</a>')

    rows.append(f'<tr><td style="padding:26px 32px 18px;border-top:1px solid #E4E4DE;">{button("Join on CampusGroups", CAMPUS, True)}{button("Follow on LinkedIn", LINKEDIN, False)}</td></tr>')
    rows.append(f'<tr><td style="padding:18px 32px 28px;font:12px/1.6 Arial,Helvetica,sans-serif;color:#8A8C9E;">'
                f'You are receiving this because you signed up for the Quinnipiac Blockchain newsletter. '
                f'This newsletter is for education only and is not financial, investment, legal, or tax advice.</td></tr>')

    label = f"Week of {today.strftime('%B')} {today.day}, {today.year}"
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Quinnipiac Blockchain newsletter</title></head>
<body style="margin:0;padding:0;background:{PAPER};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#FFFFFF;">
<tr><td style="background:{INK};padding:28px 32px;">
<div style="font:22px Georgia,serif;color:#DEDFEC;">Quinnipiac Blockchain<span style="color:{GOLD};">.</span></div>
<div style="margin-top:6px;font:13px Arial,Helvetica,sans-serif;color:#9294B3;">{esc(label)}</div></td></tr>
{chr(10).join(rows)}
</table></td></tr></table></body></html>
'''


def build_text(today, intro, news, events):
    out = [f"Subject: Quinnipiac Blockchain: this week in blockchain ({today.strftime('%b')} {today.day})", "",
           f"QUINNIPIAC BLOCKCHAIN - Week of {today.strftime('%B')} {today.day}, {today.year}", ""]
    out += [t + "\n" for t in intro]
    out += ["TOP STORIES THIS WEEK", ""]
    for n in news or []:
        out += [n["title"], f"{n.get('source', '')}", (n.get("summary") or ""), https(n["link"]), ""]
    if not news:
        out += ["No stories this week.", ""]
    if events:
        out += ["UPCOMING EVENTS", ""]
        for e in events:
            out += [e["title"], " | ".join(x for x in [e.get("dateText") or e.get("date"), e.get("location")] if x),
                    e.get("summary") or "", https(e.get("link")), ""]
    out += [f"Join on CampusGroups: {CAMPUS}", f"Follow on LinkedIn: {LINKEDIN}", "",
            "For education only. Not financial, investment, legal, or tax advice."]
    return "\n".join(x for x in out if x is not None)


def main():
    today = date.today()
    news, events = gather(today)
    intro = intro_paragraphs()
    os.makedirs(p("newsletter"), exist_ok=True)
    with open(p("newsletter", "latest.html"), "w", encoding="utf-8") as f:
        f.write(build_html(today, intro, news, events))
    with open(p("newsletter", "latest.txt"), "w", encoding="utf-8") as f:
        f.write(build_text(today, intro, news, events))
    print(f"Built newsletter: {len(news)} stories, {len(events)} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
