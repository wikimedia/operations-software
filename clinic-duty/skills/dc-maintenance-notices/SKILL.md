---
name: dc-maintenance-notices
description: Turn vendor maintenance, outage and change notification emails (datacenter, colo, transit, IX and network providers such as Equinix, Lumen, NTT, Arelion, GTT, Telxius, euNetworks, DE-CIX, SGIX, Digital Realty, Orange, CyrusOne) into one report of click-to-add Google Calendar links plus a triage summary, for SRE clinic duty. Use this whenever the user pastes or uploads one or more vendor emails, ops-maintenance threads, "planned work" / "maintenance window" / "service affecting" notices, or asks to calendar, triage, summarize, update or cancel a maintenance, even if they don't say "skill" or name the vendor. Also use when the user corrects a past result or reports a new vendor format, to improve this skill.
---

# Vendor maintenance notices -> calendar links

The user pastes or uploads one or more vendor emails (any number, mixed
vendors). They want each window on the shared maintenance calendar, and they
want **both ways in** every time: a click-to-add Google Calendar link per
window, and an `.ics` for bulk import. A human does the clicking and reviews
everything, so aim for *correct and checkable*, not fast and confident.

## Workflow

1. **Extract** each email into the schema below. Use only the email text;
   never fill vendor, site, circuit or ticket from memory.
2. **Quote evidence**: for every window, copy the exact source line(s) the
   times came from into `evidence`.
3. **Batch and run the script.** Keep ONE running JSON file for the whole
   conversation (`{"notices": [...]}`) and append each new email's notice to
   it, so every report lists *everything handled in this chat so far*, newest
   last. Never regenerate a report from the latest email alone: the user
   opens the file expecting all the maintenances, and a report with only one
   looks like the earlier ones were lost. Say in the chat summary which
   notices are new, since the user may have added the older ones already. Run:
   `python scripts/maint_to_gcal.py batch.json --out <dir>/maintenance-report.md --ics <dir>/maintenance.ics`
   (`<dir>` is `/mnt/user-data/outputs` in a chat UI, the session
   scratchpad or the directory the user names in a terminal.)
   The script does the timezone/UTC conversion, validation, duplicate
   detection and link building. Do not do time arithmetic yourself: that is
   the most likely place for a silent error, which is why it lives in code.
4. **Deliver BOTH options, always.** Every run produces the two ways of
   getting the windows onto the calendar, for *every* email handled in this
   conversation. Never deliver one and merely mention the other:
   - **click-to-add Google Calendar links**, one per window, in the report;
   - **an `.ics` file** for bulk import. Always pass `--ics`; it is not an
     optional extra. Say which one you recommend (the links, because each
     event gets a human review before Save) but hand over both.

   Links carry `crm=AVAILABLE`, so the event form opens as "Free" and
   maintenance does not block the user's calendar. (The older `trp=false`
   is ignored by the current Google Calendar and leaves the event Busy; do not
   use it.) `.ics` events are `TRANSP:TRANSPARENT` for the same reason.

   Then reply with a *short* summary: how many notices/windows, and anything
   under "Needs your attention" (missing timezone, cancellations, duplicates,
   past dates).

   Put the deliverables where the user can actually reach them, and say the
   paths out loud:
   - in a chat UI, present the report and the `.ics` with `present_files`
     and keep the long URLs out of the message; the file is the deliverable;
   - in a terminal (Claude Code and similar), a markdown link is not
     clickable and a file in a session scratchpad is easy to miss, so print
     the **raw URLs** and the **full path** of the `.ics`. There the URLs
     *are* the deliverable; a summary that only points at a file has not
     delivered anything.
5. **Never open a browser yourself.** Do not run `xdg-open`, `firefox`,
   `google-chrome`, `open`, or any browser automation to follow a calendar
   link, and do not offer to. Clicking is the human's review step and the
   whole reason the links are pre-filled forms; a sandboxed CLI will block
   the launch anyway (nono denies the browser shim). Hand over the URL or
   the file path and stop there.
6. **Never say an event was created.** The links open a pre-filled form in the
   user's browser and nothing is saved until they click Save. Only claim
   "created" if a calendar tool actually did it.

## Schema (one object per email)

```json
{
  "vendor": "Arelion",
  "ticket_id": "CRQ000000123456",
  "notice_type": "new | update | reschedule | cancel | completed | extension | unknown",
  "windows": [
    {
      "start": "2026-10-20T22:00",
      "end": "2026-10-21T04:00",
      "tz": "UTC",
      "all_day": false,
      "label": "Step 3 primary",
      "conditional": false,
      "evidence": "Service window start: 2026-10-20 22:00 UTC ..."
    }
  ],
  "sites": ["AMS1"],
  "affected_services": ["circuit IDs, ports, devices, as written"],
  "impact": "outage | at-risk | no-impact | unknown",
  "impact_text": "short quote of what the vendor says",
  "summary": "one or two plain sentences",
  "uncertain": ["anything ambiguous or missing, stated explicitly"]
}
```

- `start`/`end`: naive timestamps **exactly as written** (`YYYY-MM-DDTHH:MM`),
  no conversion. Date only, no times -> `all_day: true` with `YYYY-MM-DD`.
- `tz`: the zone **as the email states it** ("UTC", "GMT+8", "Europe/Paris",
  "+02:00"). If the email states none, use `null`. Never infer it from vendor
  or site: the script will flag it for a human instead. A silent guess is how a
  two-hour error lands on the team calendar. Use an IANA name only when the
  email names a place or you are told the site's zone.
- Several windows (per night, per step, per device) are separate entries.
  Never merge or drop them.
- Include only windows that belong to *this notice's own ticket*. Some vendors
  (DE-CIX) send one ticket per window and repeat the full multi-step schedule
  in every email body; the ticket's own window is the header one. List windows
  that belong to other tickets (with their IDs if given) in `uncertain`, not in
  `windows`, or the same slot ends up on the calendar twice.
- `label`/`conditional`: name windows as the vendor does, and set
  `conditional: true` for backup/contingency windows used only if the primary
  fails. Put any vendor rule about window reuse in `uncertain`.
- `ticket_id`: the vendor's reference; it is the key for matching later
  updates and cancellations.
- Leave a field empty and add an `uncertain` entry rather than inventing it.
- Quote vendor impact wording; don't turn "at risk" into "no impact" or back.

## Updates, reschedules, cancellations

Match on vendor + `ticket_id`. For a `cancel`, emit the notice with an empty
`windows` list: the report then says "remove the existing event" and creates no
link. For an update or reschedule, say what changed (old -> new) if the earlier
notice is in the conversation; if it isn't, say so rather than assuming. If
several notices for one ticket arrive in a batch, the script flags it so the
user can pick the latest.

## Vendor quirks and learning

`references/vendors.md` lists, per vendor, how to recognize it, the field
labels and timezone conventions seen. Read it when the vendor is identifiable,
but trust the actual email over the notes: formats change. Unknown vendors use
the same schema; no new parser is needed.

**Every new gotcha MUST be written back into this skill.** A gotcha is
anything reusable you learn from an email or a correction: a new vendor or
format, a field label or timezone rule, a ticket/window convention (e.g.
DE-CIX: one ticket per window), a mistake you made and its fix, or a link or
calendar behavior that turned out different from what you assumed. If it is
not written down, the next chat (and every teammate) will repeat the mistake.

Installed skills are read-only inside a chat, so do it this way, in the same
turn in which you find the gotcha, without waiting to be asked:
1. Fix the current output.
2. Add the lesson to `references/vendors.md` (new vendor row, or a line under
   "Gotchas learned from real emails"). If it changes how extraction or the
   script should behave in general, update this SKILL.md or the script too.
   Work in a writable copy of the skill and test the change on the email that
   exposed the problem.
3. Repackage with `python -m scripts.package_skill` (from the skill-creator
   skill) and present the new `.skill` file together with the report.
4. Tell the user plainly: "Skill updated: <one-line what changed>. Re-save the
   attached .skill over the old one, and share it with teammates." Until they
   re-save it, the lesson exists only in this chat.

Keep notes general and anonymized: record the pattern (labels, conventions),
not circuit IDs, customer names or full email bodies. Only record what an
actual email or the user's correction confirmed; mark anything you are
inferring as "unconfirmed".
