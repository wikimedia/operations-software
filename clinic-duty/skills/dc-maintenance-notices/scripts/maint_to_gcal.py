#!/usr/bin/env python3
"""Turn extracted maintenance notices into ONE report with click-to-add links.

Usage:
  maint_to_gcal.py batch.json --out /mnt/user-data/outputs/maintenance.md [--now ISO]

batch.json is either one notice object, a list of them, or {"notices": [...]}
(schema in SKILL.md). The script converts times to UTC, validates, builds
Google Calendar template links (no API, no credentials: the human's browser
session does the saving) and writes a Markdown report. It never reads emails.
Exit code: 0 on success (flags are reported inside the report), 2 on bad input.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Shared maintenance calendar used by the clinic-duty script (base64 id).
# Override with the MAINT_CALENDAR_ID environment variable or --calendar-id.
DEFAULT_CALENDAR_ID = os.environ.get(
    "MAINT_CALENDAR_ID",
    "d2lraW1lZGlhLm9yZ181OXJwOTczY243NmV2YWdzcmlxanMwZXV0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t",
)
MAX_PATH_QUERY_LEN = 16384  # Google returns 400 above this (T381680)
LONG_WINDOW = timedelta(hours=24)
OFFSET_RE = re.compile(r"^(?:UTC|GMT)?\s*([+-])(\d{1,2})(?::?(\d{2}))?$", re.I)


def parse_tz(tz):
    """tzinfo, or None if missing/unrecognized (caller flags it; never guess)."""
    if not tz:
        return None
    t = tz.strip()
    if t.upper() in ("UTC", "GMT", "Z", "UT"):
        return timezone.utc
    m = OFFSET_RE.match(t)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0)))
    try:
        return ZoneInfo(t)
    except (ZoneInfoNotFoundError, ValueError):
        return None  # e.g. "CEST": ambiguous abbreviations are not guessed


def parse_naive(s, all_day):
    try:
        return datetime.strptime(s, "%Y-%m-%d" if all_day else "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        return None


def gcal_link(calendar_id, title, location, start, end, all_day, details):
    if all_day:
        s = start.strftime("%Y%m%d")
        e = (end + timedelta(days=1) if end - start < timedelta(days=1) else end).strftime("%Y%m%d")
    else:
        s = start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        e = end.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = (
        "/calendar/event?action=TEMPLATE"
        f"&src={quote(calendar_id, safe='')}&text={quote(title, safe='')}"
        f"&location={quote(location, safe='')}"
        f"&dates={quote(s, safe='')}/{quote(e, safe='')}&crm=AVAILABLE&details="
    )

    def ok(n):
        return len(base) + len(quote(details[:n], safe="")) <= MAX_PATH_QUERY_LEN

    truncated = False
    if not ok(len(details)):
        lo, hi = 0, len(details)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        details, truncated = details[:lo], True
    return "https://www.google.com" + base + quote(details, safe=""), truncated


def process(n, calendar_id, now):
    """Return a dict describing one notice: header fields, windows, flags."""
    ntype = n.get("notice_type", "unknown")
    vendor = n.get("vendor") or "Unknown vendor"
    ticket = n.get("ticket_id") or ""
    res = {"vendor": vendor, "ticket": ticket, "type": ntype,
           "impact": n.get("impact", "unknown"), "impact_text": n.get("impact_text", ""),
           "summary": n.get("summary", ""), "sites": n.get("sites") or [],
           "affected": n.get("affected_services") or [],
           "uncertain": n.get("uncertain") or [], "flags": [], "windows": []}
    if not ticket:
        res["flags"].append("no ticket ID found: cannot be matched to updates/cancellations")
    windows = n.get("windows") or []
    if ntype == "cancel":
        res["flags"].append("CANCELLED: remove the existing calendar event(s); no new link generated")
        return res
    if not windows:
        res["flags"].append("no maintenance windows extracted")
    title = f"[{vendor}] {ticket} {res['summary']}".strip()[:110]
    location = ", ".join(res["sites"])
    for i, w in enumerate(windows, 1):
        row = {"n": i, "label": w.get("label") or "", "conditional": bool(w.get("conditional")),
               "flags": [], "link": None, "start": None, "end": None}
        res["windows"].append(row)
        all_day = bool(w.get("all_day"))
        s_naive, e_naive = parse_naive(w.get("start"), all_day), parse_naive(w.get("end"), all_day)
        if s_naive is None or e_naive is None:
            row["flags"].append("start/end could not be parsed")
            continue
        tz = parse_tz(w.get("tz"))
        if tz is None:
            row["flags"].append(f"timezone missing/unclear ({w.get('tz')!r}): NOT converted, "
                                f"as written {w.get('start')} -> {w.get('end')}; confirm manually")
            continue
        if all_day:
            start, end = s_naive, e_naive
            row["start"], row["end"] = start.date().isoformat(), end.date().isoformat() + " (all day)"
            cs, ce = start, end
        else:
            start, end = s_naive.replace(tzinfo=tz), e_naive.replace(tzinfo=tz)
            cs, ce = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
            row["start"], row["end"] = cs.strftime("%Y-%m-%d %H:%M"), ce.strftime("%Y-%m-%d %H:%M")
        if ce < cs:
            row["flags"].append("end is before start")
            continue
        if not all_day and ce - cs > LONG_WINDOW:
            row["flags"].append("window longer than 24h")
        if not all_day and ce < now:
            row["flags"].append("window is in the past")
        wtitle = title + (f" - {row['label']}" if row["label"] else "") + \
            (" [BACKUP, only if needed]" if row["conditional"] else "")
        details = (f"{res['summary']}\n\nImpact: {res['impact']} - {res['impact_text']}\n"
                   f"Affected: {'; '.join(res['affected'])}\n\nSource evidence:\n- {w.get('evidence', '')}"
                   + "".join(f"\nNote: {u}" for u in res["uncertain"]))
        row["ics"] = {"uid": f"{ticket or vendor}-{i}-{row['label']}".replace(" ", "-"),
                      "title": wtitle, "location": location, "details": details,
                      "start": start, "end": end, "all_day": all_day}
        row["link"], trunc = gcal_link(calendar_id, wtitle, location, start, end, all_day, details)
        if trunc:
            row["flags"].append("calendar details truncated to fit URL limit")
    return res


def _esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    out = []
    while len(line) > 75:
        out.append(line[:75])
        line = " " + line[75:]
    out.append(line)
    return out


def render_ics(results, now):
    """iCalendar file; events are TRANSPARENT (show as available, not busy)."""
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//dc-maintenance-notices//EN", "CALSCALE:GREGORIAN"]
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    for r in results:
        for w in r["windows"]:
            e = w.get("ics")
            if not e:
                continue
            if e["all_day"]:
                end = e["end"] + timedelta(days=1) if e["end"] - e["start"] < timedelta(days=1) else e["end"]
                dt = [f"DTSTART;VALUE=DATE:{e['start'].strftime('%Y%m%d')}",
                      f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}"]
            else:
                dt = [f"DTSTART:{e['start'].astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
                      f"DTEND:{e['end'].astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"]
            ev = ["BEGIN:VEVENT", f"UID:{e['uid']}@dc-maintenance-notices", f"DTSTAMP:{stamp}"] + dt + [
                f"SUMMARY:{_esc(e['title'])}", f"LOCATION:{_esc(e['location'])}",
                f"DESCRIPTION:{_esc(e['details'])}",
                "STATUS:" + ("TENTATIVE" if w["conditional"] else "CONFIRMED"),
                "TRANSP:TRANSPARENT", "END:VEVENT"]
            for line in ev:
                L += _fold(line)
    L.append("END:VCALENDAR")
    return "\r\n".join(L) + "\r\n"


def render(results, now):
    seen = {}
    for r in results:
        if r["ticket"]:
            seen.setdefault((r["vendor"], r["ticket"]), []).append(r)
    for (v, t), rs in seen.items():
        if len(rs) > 1:
            rs[-1]["flags"].append(f"ticket appears {len(rs)}x in this batch: later notices may "
                                   "supersede earlier ones, check before adding")
    attention = []
    for r in results:
        who = f"{r['vendor']} {r['ticket']}".strip()
        attention += [f"**{who}**: {f}" for f in r["flags"]]
        for w in r["windows"]:
            wl = f"window {w['n']}" + (f" ({w['label']})" if w["label"] else "")
            attention += [f"**{who}**, {wl}: {f}" for f in w["flags"]]
    out = [f"# Maintenance report ({len(results)} notice{'s' * (len(results) != 1)})",
           f"_Generated {now.strftime('%Y-%m-%d %H:%M')} UTC. All times UTC. Links open a pre-filled "
           "Google Calendar form in your browser; nothing is saved until you click Save._", ""]
    if attention:
        out += ["## Needs your attention", ""] + [f"- {a}" for a in attention] + [""]
    for r in results:
        who = f"{r['vendor']} {r['ticket']}".strip()
        out += [f"## {who}: {r['type']}, impact: {r['impact']}", ""]
        if r["summary"]:
            out += [r["summary"], ""]
        if r["sites"]:
            out.append(f"- **Sites:** {', '.join(r['sites'])}")
        if r["affected"]:
            out.append(f"- **Affected:** {'; '.join(r['affected'])}")
        if r["impact_text"]:
            out.append(f"- **Vendor says:** {r['impact_text']}")
        for u in r["uncertain"]:
            out.append(f"- **Uncertain:** {u}")
        out.append("")
        if r["windows"]:
            out += ["| # | Window | Start (UTC) | End (UTC) | Calendar |", "|---|---|---|---|---|"]
            for w in r["windows"]:
                label = w["label"] or ""
                lab = label or "-"
                if w["conditional"] and "backup" not in label.lower():
                    lab += " (backup)"
                link = f"[Add to calendar]({w['link']})" if w["link"] else "not available (see above)"
                out.append(f"| {w['n']} | {lab} | {w['start'] or '?'} | {w['end'] or '?'} | {link} |")
            out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", required=True, help="report path (.md)")
    ap.add_argument("--ics", help="also write an .ics (events marked available/free)")
    ap.add_argument("--calendar-id", default=DEFAULT_CALENDAR_ID)
    ap.add_argument("--now", help="ISO UTC time to treat as now (tests)")
    a = ap.parse_args()
    try:
        with open(a.path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    notices = data.get("notices") if isinstance(data, dict) and "notices" in data else \
        (data if isinstance(data, list) else [data])
    if not notices or not all(isinstance(n, dict) for n in notices):
        print("input must be a notice object, a list of them, or {'notices': [...]}", file=sys.stderr)
        return 2
    now = datetime.fromisoformat(a.now).replace(tzinfo=timezone.utc) if a.now else datetime.now(timezone.utc)
    results = [process(n, a.calendar_id, now) for n in notices]
    with open(a.out, "w") as f:
        f.write(render(results, now) + "\n")
    if a.ics:
        with open(a.ics, "w", newline="") as f:
            f.write(render_ics(results, now))
    links = sum(1 for r in results for w in r["windows"] if w["link"])
    flagged = sum(1 for r in results if r["flags"] or any(w["flags"] for w in r["windows"]))
    print(f"wrote {a.out}: {len(results)} notices, {links} calendar links, {flagged} notices with flags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
