# Vendor notes

Derived from the regexes in `operations-software/clinic-duty/ops-maint-gcal.js`.
These are hints for locating fields, NOT guarantees. Verify against the email.
Last reviewed against the repo, not against current live emails.

| Vendor | How to recognize | Time fields (label) | TZ convention | Location / impact hints |
|---|---|---|---|---|
| Equinix | "Equinix Customer" | `DATE:` line, span `A - B` | UTC; date only, no times -> treat as all-day | `IBX(s):` |
| Lumen | "Lumen Connect" | "Start"/"End" with date then `(...)` | not stated in parser; check email | `Location(s):` |
| NTT | `noc@ntt.net`, `coins@gin.ntt.net` | `Start Date/Time:` / `End Date/Time:` | UTC | "Affected Services" block |
| Arelion | "Arelion", MyArelion portal | `Service window start:` / `end:` | zone written inline on those lines (UTC seen). Can have multiple windows | `Location:` |
| Orange | "Orange customer" | `Beginning: <date> at <time>` / `End:` | UTC | `Impact:` (no real location) |
| Telxius | `@telxius.com` | `SCHEDULE` section, `A - B` | UTC | `LOCATION` |
| euNetworks | "euNetworks Change" | `Start Time:` / `End Time:` | not stated; check email | `Location Description:` |
| SGIX | `@sgix.sg` | `Start Time: <date> at <time> hrs` | GMT+8 | site codes like `SG123` |
| DE-CIX | `support@de-cix.net` | `Work start:` / `Work end:` | not stated; check email | `Devices:` |
| Digital Realty | `ecc@digitalrealty.com` | `Time Start:` / `Time End:` "... Local time" | **Local time of the site.** The old parser assumed GMT+2, which is wrong across DST and other sites. Ask which site | `Site Location:` |
| GTT | `netopsadmin@gtt.net` | `Start` / `End` ... GMT | GMT | `Location` ... `Planned` |
| CyrusOne | (not implemented upstream, `XXX add cyrusone`) | unknown | unknown | unknown |

Known gaps upstream worth handling here: multiple windows per notice
(Arelion), cancellations/updates (none handled), sites whose local time zone
is not the one assumed.

## Gotchas learned from real emails

- **DE-CIX** (DXDB:MAINT): one ticket per window. The header `Work start` /
  `Work end` is the ticket's own window; the "Schedule:" section in the body
  repeats ALL windows of the multi-step plan (Step 3 primary/backup, Step 4
  primary/backup), each of which has its own ticket (e.g. 3755 = Step 3
  primary, 3756 = Step 3 backup). Create events only for the header window.
  Impact is `Impact: FYI` plus a sentence. Site is
  `Site: DE-CIX <city> (all devices)`, not a `Devices:` line. Backup windows
  are conditional; if Step 3 succeeds in its primary window, the Step 3 backup
  slot becomes the Step 4 primary window.
- **Arelion** (PWIC): the opposite of DE-CIX. One `Planned work reference:
  PWIC<n> (Multiple service windows)` owns every window in the mail; each is a
  `Service Window: PWIC<n>.<k> <primary|additional>` block with its own
  `Work Status:` (`Confirmed` = upcoming, `Implemented` = done) and its own
  `Service window start:` / `end:` lines carrying the zone inline. Use the
  parent `PWIC<n>` as `ticket_id` and put `.k` plus its wording in the window
  `label`; extract all of them. "additional" windows are *not* backup/
  contingency slots in the DE-CIX sense, so leave `conditional: false` unless
  the mail says a window is only used if another fails.
- **Arelion update mails** restate the full schedule and change only the
  `Work Status:` of the window being reported (subject/first line reads
  "Update: ... has been completed"). Keep `notice_type: update`, keep the
  already-implemented window in `windows` but say "COMPLETED, do not add" in
  its label so the generated link is self-documenting; the script's "window is
  in the past" flag then surfaces it under "Needs your attention". The
  actionable windows are the ones still `Confirmed`.
- Impact lives in two places in Arelion mails: a prose `Action and Reason:`
  sentence ("Service is only AT RISK...") and a per-service
  `Impacted Services / Estimated Impact` table. Quote both; they agree so far,
  but the table is the authoritative per-circuit one.
- `Location:` can be a bare city/state with a trailing comma ("Atlanta/GA,").
  It is a place, not a site code, and it is *not* a timezone source — Arelion
  states the zone on the window lines, so never derive one from the location.
- **Arelion** single-window mails drop the "(Multiple service windows)" suffix:
  the header is just `Planned work reference: PWIC<n>` with one
  `Service Window: PWIC<n>.1 primary` block. Same structure, same handling —
  the parent `PWIC<n>` is still the `ticket_id`.
- **Orange**: the ticket reference lives in the *subject* ("Service Impacting
  Change No CAB N° T<digits>"); the body has no reference field, only
  `Type:` / `Nature:` / `Cause:`. Times are `Beginning:` / `End:` as
  `<Weekday> DD/Mon/YYYY at HH:MM (UTC)` with the zone in parentheses, plus a
  `Duration:` to cross-check. `Impact: Complete failure` means a full outage
  (map to `outage`, not at-risk). The two product tables ("critical product" /
  "other product") often carry `- - -` in the Sites and Corporate name columns,
  so there is genuinely no location — leave `sites` empty and note it rather
  than deriving a site from the product ID or IP. Columns run together in the
  plaintext copy: record product type/ID and whatever is under `Ends` (an IP,
  an AS number) verbatim in `affected_services` without interpreting them.
- **Equinix** (Service Insight / Global Service Desk mails) give the window
  four times: `DATE:` and `SPAN:` carry the dates *with the year* but no times,
  then `LOCAL:` and `UTC:` carry weekday + day + month + times but **no year**.
  Use the `UTC:` line for the window and take the year from `DATE:`/`SPAN:` —
  do not treat the date-only `DATE:` line as an all-day event when `LOCAL:`/
  `UTC:` times are present. The `LOCAL:` line is a free cross-check of the IBX
  zone (e.g. SG3 = UTC+8); if LOCAL and UTC disagree, flag it instead of
  picking one. Site is `IBX:` (singular here, `IBX(s):` elsewhere). The change
  reference is in the closing prose — "Please reference CHG<digits>" — not in a
  labelled field. Impact is prose only, no per-service table: redundancy +
  failover wording with "may experience minor or no impact" is `at-risk`, not
  `no-impact`, even when the mail also says no impact is expected.
