import requests
import re
import datetime
from collections import defaultdict
import time
try:
    import pywikibot
    no_pywikibot = False
except BaseException:
    no_pywikibot = True

phab_title_cache = {}
DBAs = {
    'marostegui': 'marostegui',
    'kormat': 'kormat',
    'jynus': 'jynus',
    'Amir1': 'ladsgroup'
}


def get_phab_title(tid):
    global phab_title_cache
    if tid in phab_title_cache:
        return phab_title_cache[tid]
    # It should use conduit but it requires token and all that jazz.
    # Overkill for this
    content = requests.get('https://phabricator.wikimedia.org/' + tid).text
    title = re.findall(
        r'<title>(.+?)</title>',
        content)[0].replace(
        '⚓',
        '').replace(
            tid,
        '').strip()
    phab_title_cache[tid] = title
    return phab_title_cache[tid]


def build_report(per_dc_per_section):
    report = ''
    for dc in ['eqiad', 'codfw']:
        # To keep the order consistent
        if dc not in per_dc_per_section:
            continue
        report += '{{| class="wikitable"\n|+ {}\n|-\n! Section !! Work\n|-\n'.format(
            dc)
        for i in sorted(per_dc_per_section[dc].items(), key=lambda d: d[0]):
            section = i[0]
            cases = sorted(list(set(per_dc_per_section[dc][section])))
            if len(cases) == 1:
                report += '| {} || {}\n|-\n'.format(section, cases[0])
            else:
                report += '| {} || {}\n|-\n'.format(
                    section, '\n* ' + '\n* '.join(cases))
        report += '|}\n'
    return report


def format_case(case):
    case = case.split('@')
    return '[[phab:{}|{} ({})]] ({})'.format(case[1], get_phab_title(case[1]),
                                             case[1], case[0])


def transform_section_repot(section_changes):
    # Fast
    per_dc_per_section = defaultdict(dict)
    for section in section_changes:
        if section.count('/') != 2:
            continue
        dc = section.split('/')[0]
        section_name = section.split('/')[2]
        if dc not in ['eqiad', 'codfw']:
            continue
        if not re.findall(r'^[a-z]{,2}\d$', section_name):
            continue
        per_dc_per_section[dc][section_name] = per_dc_per_section[dc].get(section_name, [])
        for case in section_changes[section]:
            per_dc_per_section[dc][section_name].append(format_case(case))
            per_dc_per_section[dc][section_name] = sorted(per_dc_per_section[dc][section_name])

    return per_dc_per_section


def build_section_report(sal):
    # Slow
    section_changes = defaultdict(set)
    for line in sal:
        if 'dbctl commit ' in line:
            phab_tickets = set(re.findall(r'T\d+', line))
            user = re.findall(r'(\S+)@cumin', line)
            phab_paste = re.findall(
                r'diff saved to https://phabricator.wikimedia.org/P(\d+)', line)
            if not phab_tickets or len(
                    user) != 1 or len(phab_paste) != 1:
                continue
            r = requests.get(
                'https://phabricator.wikimedia.org/paste/raw/{}/'.format(phab_paste[0]))
            section = re.findall(r'\n\s*\+*?\s*?(\S+?) generated', r.text)
            if not section or len(set([i.split('/')[-1]
                                  for i in section])) != 1:
                print(section, r.text, line)
                continue
            section[0] = section[0].replace('DEFAULT', 's3')
            for phab_ticket in phab_tickets:
                section_changes[section[0]].add(
                    '{}@{}'.format(user[0], phab_ticket))
        if 'dbmaint' in line:
            line = re.sub(r'\d\d\:\d\d', '', line)
            phab_tickets = set(re.findall(r'T\d+', line))
            if not phab_tickets:
                print('no phab')
                continue
            user = line.split(':')[0]
            for valid_user in DBAs:
                if valid_user in user:
                    user = DBAs[valid_user]
                    break
            else:
                print('no user', user)
                continue
            sections = set(re.findall(r'\b((?:s|es|pc|m|x)\d+)\b', line))
            if not sections:
                print('no sections')
                continue
            dcs = set(re.findall(r'\b(eqiad|codfw)\b', line))
            if not dcs:
                print('no dcs')
                continue
            for dc in dcs:
                for phab_ticket in phab_tickets:
                    for section in sections:
                        section_changes['{}/foo/{}'.format(dc, section)].add(
                            '{}@{}'.format(user, phab_ticket))

    return section_changes


def get_day_sal(text, date):
    sal = re.split(r'\=\=\s*?' + date + r'\s*?\=\=\n', text)
    if len(sal) != 2:
        return []
    sal = sal[1].split('\n==')[0]
    return set(sal.split('\n'))


def merge(a, b):
    c = {}
    for i in a:
        c[i] = a[i].union(b.get(i, set()))
    for i in b:
        if i in a:
            continue
        c[i] = b[i]
    return c


per_day_data = {}
per_day_sal = {}


def get_per_day_data(text, date):
    global per_day_data, per_day_sal
    sal = get_day_sal(text, date)
    if date in per_day_sal:
        diffed_sal = set(sal) - set(per_day_sal[date])
    else:
        diffed_sal = sal
    if diffed_sal:
        diffed_section_report = build_section_report(diffed_sal)
    else:
        diffed_section_report = {}
    per_day_sal[date] = sal

    per_day_data[date] = merge(
        per_day_data.get(
            date, {}), diffed_section_report)
    return per_day_data[date]


def handle_day(date, name, text):
    data = get_per_day_data(text, date)
    print('== {} ({}) ==\n'.format(name, date) +
          build_report(transform_section_repot(data)))


def get_day(i):
    if i == 0:
        return datetime.datetime.now().strftime("%Y-%m-%d")
    date = datetime.date.today() - datetime.timedelta(days=i)
    return date.strftime("%Y-%m-%d")


if not no_pywikibot:
    wikitech = pywikibot.Site('en', 'wikitech')
    wikitech.login()
while True:
    if no_pywikibot:
        text = requests.get(
            'https://wikitech.wikimedia.org/wiki/Server_Admin_Log?action=raw').text
    else:
        sal_page = pywikibot.Page(wikitech, 'Server_Admin_Log')
        text = sal_page.get()
    data = get_per_day_data(text, get_day(0))
    final_result = '{{{{/Header}}}}\n== Today ({}) ==\n'.format(
        get_day(0)) + build_report(transform_section_repot(data))
    data = get_per_day_data(text, get_day(1))
    final_result += '== Yesterday ({}) ==\n'.format(get_day(1)) + \
        build_report(transform_section_repot(data))
    last_seven_days_data = {}
    for i in range(7):
        last_seven_days_data = merge(
            last_seven_days_data, get_per_day_data(
                text, get_day(i)))
    final_result += '== Last seven days ==\n' + \
        build_report(transform_section_repot(last_seven_days_data))
    if no_pywikibot:
        print(final_result)
    else:
        report_page = pywikibot.Page(wikitech, 'Map of database maintenance')
        if report_page.get() != final_result:
            report_page.put(final_result, summary='Bot: Updating the report')
    time.sleep(180)
