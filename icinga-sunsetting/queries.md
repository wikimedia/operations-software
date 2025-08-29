# Queries executed by audit.py

## Dump Nrpe::Monitor_service resources
```
curl -G -H "Accept: application/json" http://localhost:8080/pdb/query/v4/resources \
 --data-urlencode 'query=["=","type", "Nrpe::Monitor_service"]' | \
jq -r '
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
' | sort | uniq > nrpe_checks.csv
```

## Dump monitoring::Check_prometheus
```
curl -G -H "Accept: application/json" \
http://localhost:8080/pdb/query/v4/resources \
  --data-urlencode 'query=["=","type", "Monitoring::Check_prometheus"]' | \
jq -r '
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
    $parameters.migration_task,
    $file,
    $line
  ]
| @csv
' | sort | uniq > prometheus_checks.csv
```

## Dump pure Monitoring::Service resources
```
curl -G -H "Accept: application/json" \
http://localhost:8080/pdb/query/v4/resources \
  --data-urlencode 'query=["=","type", "Monitoring::Service"]' | \
jq -r '
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
' | sort | uniq > monitoring_services.csv
```


