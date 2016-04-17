#!/bin/bash

function usage() {
    cat << USAGE
Usage: ${0} -s START_TIMESTAMP -e END_TIMESTAMP -r REVISION_DB -o ORIGIN_DB
       -t TARGET_DB -c CLUSTER -d DATABASES_FILE

Example: ${0} -s 20160131235959 -e 20160201020000 -r dbstore1002.eqiad.wmnet
         -o es1019.eqiad.wmnet -t es2019.codfw.wmnet -c 25 -d databases.txt

External Storage check script to ensure that the content of a group of blobs id
and text content is the same between the ORIGIN_DB server and the TARGET_DB one
for all revisions created between START_TIMESTAMP and END_TIMESTAMP for the
given CLUSTER.
The revision table to get the timestamps is checked on the REVISION_DB server.
DATABASES_FILE is expected to be a file with all the databases to be checked,
one per line.
Timestamps must be in the format used by MediaWiki: YYYYmmddHHMMSS
All parameters are mandatory.
USAGE
    exit 1
}

function delta_time() {
    echo "$(date +"%s.%N") ${START}" | awk '{printf "%.3f", $1 - $2}'
}

while getopts ":s:e:r:o:t:c:d:" OPT; do
    case ${OPT} in
        s) START_TIMESTAMP="${OPTARG}" ;;
        e) END_TIMESTAMP="${OPTARG}" ;;
        r) REVISION_DB="${OPTARG}" ;;
        o) ORIGIN_DB="${OPTARG}" ;;
        t) TARGET_DB="${OPTARG}" ;;
        c) CLUSTER="${OPTARG}" ;;
        d) DATABASES_FILE="${OPTARG}" ;;
        \?)
            echo "Invalid option: -${OPTARG}" >&2
            usage
            ;;
        :)
            echo "Option -${OPTARG} requires an argument." >&2
            usage
            ;;
    esac
done

if [[ -z "${START_TIMESTAMP}" ]]; then
    echo "Missing mandatory argument -s START_TIMESTAMP"
    usage
fi

if [[ -z "${END_TIMESTAMP}" ]]; then
    echo "Missing mandatory argument -e END_TIMESTAMP"
    usage
fi

if [[ -z "${REVISION_DB}" ]]; then
    echo "Missing mandatory argument -r REVISION_DB"
    usage
fi

if [[ -z "${ORIGIN_DB}" ]]; then
    echo "Missing mandatory argument -o ORIGIN_DB"
    usage
fi

if [[ -z "${TARGET_DB}" ]]; then
    echo "Missing mandatory argument -t TARGET_DB"
    usage
fi

if [[ -z "${CLUSTER}" ]]; then
    echo "Missing mandatory argument -c CLUSTER"
    usage
fi

if [[ -z "${DATABASES_FILE}" || ! -e "${DATABASES_FILE}" ]]; then
    echo "Missing mandatory argument -d DATABASES_FILE or DATABASES_FILE does not exists"
    usage
fi

COUNT=0
OK=0
NO_REV=0
DIFF=0
NO_BLOB=0
ERROR=0
INVERTED=0

while read DB; do
    START="$(date +"%s.%N")"
    COUNT=$((COUNT + 1))

    echo -n "Checking ${DB}: "
    MIN_PAGE="$(mysql -h "${REVISION_DB}" --batch --skip-column-names -e "SELECT rev_text_id FROM revision WHERE rev_timestamp > '${START_TIMESTAMP}' LIMIT 1" "${DB}")"
    if [[ "${?}" -ne "0" ]]; then
        ERROR=$((ERROR + 1))
        echo "Unable to get revisions ($(delta_time)s)"
        continue
    fi

    MAX_PAGE="$(mysql -h "${REVISION_DB}" --batch --skip-column-names -e "SELECT rev_text_id FROM revision WHERE rev_timestamp > '${END_TIMESTAMP}' LIMIT 1" "${DB}")"

    if [[ -z "${MIN_PAGE}" || -z "${MAX_PAGE}" || "${MIN_PAGE}" == "${MAX_PAGE}" ]]; then
        NO_REV=$((NO_REV + 1))
        echo "No revisions to analyze ($(delta_time)s)"
        continue
    fi

    MIN_BLOB="$(mysql -h "${REVISION_DB}" --batch --skip-column-names -e "SELECT SUBSTRING_INDEX(old_text, '/', -1) FROM text WHERE old_id = ${MIN_PAGE}" "${DB}")"
    MAX_BLOB="$(mysql -h "${REVISION_DB}" --batch --skip-column-names -e "SELECT SUBSTRING_INDEX(old_text, '/', -1) FROM text WHERE old_id = ${MAX_PAGE}" "${DB}")"

    if [[ -z "${MIN_BLOB}" || -z ${MAX_BLOB} ]]; then
        NO_BLOB=$((NO_BLOB + 1))
        echo "Unable to find blob_id for revision ${MIN_PAGE} or ${MAX_PAGE} ($(delta_time)s)"
        continue
    fi

    if [[ "${MIN_BLOB}" -gt "${MAX_BLOB}" ]]; then
        INVERTED=$((INVERTED + 1))
        echo -n "INVERTED "
        TMP_BLOB="${MIN_BLOB}"
        MIN_BLOB="${MAX_BLOB}"
        MAX_BLOB="${TMP_BLOB}"
    fi

    # Get from origin
    mysql -h "${ORIGIN_DB}" --batch --skip-column-names -e "SELECT blob_id, MD5(blob_text) FROM blobs_cluster${CLUSTER} WHERE blob_id BETWEEN ${MIN_BLOB} AND ${MAX_BLOB}" "${DB}" > "${DB}_${ORIGIN_DB}.out"
    # Get from target
    mysql -h "${TARGET_DB}" --batch --skip-column-names -e "SELECT blob_id, MD5(blob_text) FROM blobs_cluster${CLUSTER} WHERE blob_id BETWEEN ${MIN_BLOB} AND ${MAX_BLOB}" "${DB}" > "${DB}_${TARGET_DB}.out"

    # Compare
    diff -q "${DB}_${ORIGIN_DB}.out" "${DB}_${TARGET_DB}.out"
    if [[ "${?}" -eq "0" ]]; then
        OK=$((OK + 1))
        echo "OK ($(delta_time)s)"
    else
        DIFF=$((DIFF + 1))
        echo "DIFF ($(delta_time)s)"
    fi

    sleep 1

done < "${DATABASES_FILE}"

echo "==== SUMMARY ===="
echo "Analyzed ${COUNT} wikis"
echo "rev_text_id needed to be inverted for ${INVERTED} wikis"
echo "OK: ${OK} wikis"
echo "No revisions to check: ${NO_REV} wikis"
echo "No blob found for revision: ${NO_BLOB} wikis"
echo "With differences: ${DIFF} wikis"
echo "With error getting revisions: ${ERROR} wikis"

exit 0

