# dc-maintenance-notices (Claude skill)

A [Claude skill](https://docs.claude.com) for SRE clinic duty: paste vendor
maintenance emails (DCs, transit, IXPs, network providers) into a chat and get
back **one report with click-to-add Google Calendar links**, plus an optional
`.ics` for bulk import. It is an alternative to `../ops-maint-gcal.js`
(which keeps working unchanged): instead of one regex parser per vendor, Claude
extracts the data and a small deterministic script does the time handling.

## How it works

1. Claude extracts each email into a small JSON schema (vendor, ticket,
   windows with the timezone *as written*, sites, impact, evidence quotes).
2. `dc-maintenance-notices/scripts/maint_to_gcal.py` converts times to UTC,
   validates, detects duplicates/cancellations, and writes
   `maintenance-report.md` (and optionally `maintenance.ics`). Timezones are
   never guessed: a missing or ambiguous one is flagged and no link is made.
3. A human opens the report, clicks "Add to calendar", checks the pre-filled
   form and clicks Save. Nothing is written to a calendar automatically.
   Links carry `crm=AVAILABLE` so events show as Free, not Busy.

The script does not read emails and has no credentials; it only builds URLs.

## Install and use

1. Build the package: `python3 build_skill.py` (-> `dist/dc-maintenance-notices.skill`)
   and add it in Claude (Save skill button on the file card, or the Skills
   settings).
2. In a chat, paste or upload any number of vendor emails. Open the returned
   `maintenance-report.md` and click the links. Read the "Needs your
   attention" section first.

## Layout

```
dc-maintenance-notices/        the skill (this folder is what gets packaged)
  SKILL.md                     instructions Claude follows
  scripts/maint_to_gcal.py     UTC conversion, validation, gcal links, .ics
  references/vendors.md        per-vendor formats + gotchas learned from real emails
tests/                         unit tests (Python stdlib) and a real-notice fixture
build_skill.py                 builds dist/dc-maintenance-notices.skill
```

## Updating the skill (gotchas)

Every new vendor format or pitfall must be recorded in
`dc-maintenance-notices/references/vendors.md` ("Gotchas learned from real
emails"). In a Claude chat, Claude hands back a new `.skill` after each such
discovery: copy the changed files over this folder, review the diff, add a test
if behavior changed, commit, and re-save the `.skill` in Claude so teammates get
it. Keep notes general: no circuit IDs, customer names or full email bodies.

## Development

```
python3 -m unittest discover -s tests -v     # Python 3.9+, stdlib only
python3 build_skill.py
python3 dc-maintenance-notices/scripts/maint_to_gcal.py tests/fixtures/decix_3755_3758.json \
  --out /tmp/maintenance-report.md --ics /tmp/maintenance.ics
```

The shared calendar id defaults to the one used by `ops-maint-gcal.js`;
override it with `MAINT_CALENDAR_ID` or `--calendar-id`.

## Privacy

Vendor emails can contain circuit IDs and site details. Check your policy
before pasting them into any external service, and keep them out of this
repository (including test fixtures).
