#!/usr/bin/env python3

import pandas as pds
import re
import csv
import click
import sys
import json
import jq

from pypuppetdb import connect
from box import Box
from collections import defaultdict

RTYPES = [
    {
        "rtype": "Nrpe::Monitor_service",
        "filter": """
.[]
| select(.file | startswith("/etc") | not)
| .title as $title
| .parameters as $parameters
| .file as $file
| .line as $line
| [
    ([.tags[] | select(startswith("profile:"))] | sort)
    | ($title),
    "Nrpe::Monitor_service",
    (
      if ($parameters.nrpe_command | startswith("/usr/bin/sudo"))
      then ($parameters.nrpe_command | split(" ")[0:2] | join(" "))
      else ($parameters.nrpe_command | split(" ")[0])
      end
    ),
    (. | join("|")),
    $parameters.migration_task,
    $file,
    $line
  ]
| @csv
""",
    },
    {
        "rtype": "Monitoring::Service",
        "filter": """
.[]
| select(.parameters.check_command | startswith("nrpe_check") | not)
| select(.parameters.check_command | startswith("check_prometheus") | not)
| .title as $title
| .parameters as $parameters
| .file as $file
| .line as $line
| [
    ([.tags[] | select(startswith("profile:"))] | sort)
    | ($title),
    "Monitoring::Service",
    ($parameters.check_command | split("!")[0]),
    (. | join("|")),
    $parameters.migration_task,
    $file,
    $line
  ]
| @csv
""",
    },
    {
        "rtype": "Monitoring::Check_prometheus",
        "filter": """
.[]
| select(.file | startswith("/etc") | not)
| .title as $title
| .parameters as $parameters
| .file as $file
| .line as $line
| [
    ([.tags[] | select(startswith("profile:"))] | sort)
    | ($title),
    "Monitoring::Check_prometheus",
    "promql",
    (. | join("|")),
    "None",
    $file,
    $line
  ]
| @csv
""",
    },
]


def pdbquery(db, rtype, jqfilter):

    pql = f"""
    resources [title, parameters, tags, file, line]{{
        type = '{rtype}'
    }}
    """

    resources = jq.compile(jqfilter).input_value(list(db.pql(pql))).all()

    return resources


def make_inner_dict():
    return {"titles": [], "profiles": set()}


def generalize(strings, placeholder="X", debug=False):
    pattern = r"[a-zA-Z0-9]+|[^a-zA-Z0-9]"
    patternwosep = r"[a-zA-Z0-9]+"
    maxlen = 0
    maxstr = re.findall(pattern, strings[0])
    for s in strings:
        segs = re.findall(pattern, s)
        lsegs = len(segs)
        if lsegs >= maxlen:
            maxlen = lsegs
            maxstr = segs

    if debug:
        print(json.dumps({"generalize_maxstr": maxstr}, indent=2), file=sys.stderr)

    generalized = []
    for seg in maxstr:
        common = True
        for s in strings:
            if seg not in re.findall(patternwosep, s):
                common = False
                break
        if (common) or (len(re.findall(patternwosep, seg)) == 0):
            generalized.append(seg)
        else:
            generalized.append(placeholder)

    return re.sub(r"(X(?:[^a-zA-Z0-9]X)+)", placeholder, "".join(generalized))


@click.command()
@click.option(
    "--input-file",
    required=True,
    help="""
Input file to parse.
Mandatory format: title, resourcetype, command, profiles, task, file, line.
The profiles field is a pipe-separated list of profiles.
If invoked with --resource-list-update, the file may not exist; in that case,
it will be created and updated by querying PuppetDB on localhost.
""",
)
@click.option(
    "--resource-list-update",
    is_flag=True,
    default=False,
    help="Force a query to PuppetDB on localhost to update the input file in place.",
)
@click.option("--debug", is_flag=True, default=False, help="Print verbose debug ouput")
def main(input_file, resource_list_update, debug):
    """Query PuppetDB on localhost to produce a list of all Icinga checks defined in Puppet.
    The list will be deduplicated based on where the checks are physically declared,
    and a heuristic is applied to the resource titles to approximate which parts of the titles are parameterized.
    """

    if resource_list_update:
        # ssh puppetdb1003.eqiad.wmnet -L 8080:localhost:8080
        db = connect()

        res = set()
        for e in RTYPES:
            eb = Box(e)
            r = pdbquery(db, eb.rtype, eb.filter)
            for i in r:
                res.add(i)

        with open(input_file, "w") as f:
            f.write("\n".join(res))

    groups = defaultdict(make_inner_dict)
    df = pds.read_csv(input_file, sep=",")
    df.columns = [
        "title",
        "resourcetype",
        "command",
        "profiles",
        "task",
        "file",
        "line",
    ]
    df = df.fillna("Missing")
    df = df.astype(
        {
            "title": "string",
            "resourcetype": "string",
            "command": "string",
            "profiles": "string",
            "task": "string",
            "file": "string",
            "line": "int64",
        }
    )

    def group(entry):
        e = Box(entry.to_dict())
        groups[f"{e.resourcetype}#{e.command}#{e.task}#{e.file}#{e.line}"][
            "titles"
        ].append(e.title)
        for p in e.profiles.split("|"):
            groups[f"{e.resourcetype}#{e.command}#{e.task}#{e.file}#{e.line}"][
                "profiles"
            ].add(p)

    df.apply(group, axis=1)

    outraw = []
    for k, v in groups.items():
        bv = Box(v)
        resourcetype, command, task, file, line = k.split("#")
        if debug:
            print(
                json.dumps(
                    {
                        "titles": bv.titles,
                        "title": generalize(bv.titles, debug=debug),
                        "resourcetype": resourcetype,
                        "command": command,
                        "profiles_list": list(bv.profiles),
                        "profiles": "|".join(list(bv.profiles)),
                        "task": task,
                        "file": file,
                        "line": line,
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
        outraw.append(
            {
                "title": generalize(bv.titles, debug=debug),
                "resourcetype": resourcetype,
                "command": command,
                "profiles": "|".join(list(bv.profiles)),
                "task": task,
                "file": file,
                "line": line,
            }
        )

    odf = pds.DataFrame(outraw)
    odf = odf.astype(
        {
            "title": "string",
            "resourcetype": "string",
            "command": "string",
            "profiles": "string",
            "task": "string",
            "file": "string",
            "line": "int64",
        }
    )

    print(
        odf.to_csv(
            index=False, header=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC
        )
    )


if __name__ == "__main__":
    main()
