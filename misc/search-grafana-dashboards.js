#!/usr/bin/node

/*
    Copyright (C) 2022 Timo Tijhof
                       Wikimedia Foundation

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; version 2
    of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

// Browser usage, after pasting this file into the console:
//
//     search('wanobjectcache')
//     search('mediawiki_(http|rate)')
//
// Node.js usage (Node 18 or higher is required):
//
//     $ node ./search-grafana-dashboards.js 'mediawiki_(http|rate)'
//
async function search(pattern) {
	const urlListQuery = 'https://grafana.wikimedia.org/api/search?query=&starred=false';
	const urlDashApiBase = 'https://grafana.wikimedia.org/api/dashboards/uid/';
	const urlBase = 'https://grafana.wikimedia.org';
	const urlAlertQuery = 'https://grafana.wikimedia.org/api/ruler/grafana/api/v1/rules?subtype=cortex';
	const API_BATCH_SIZE = 30;
	const PROGRESS_CHUNK = API_BATCH_SIZE;

	const rPattern = new RegExp('[^"\')}]*?' + pattern + '[^"\')}]*', 'g');
	console.info('Searching for: ' + rPattern);

	// start fetches in parallel, await later
	const listFetch = fetch(urlListQuery);
	const alertsFetch = fetch(urlAlertQuery);

	const listResp = await listFetch;
	const list = await listResp.json();
	const dashes = list.filter(item => item.type == 'dash-db');
	const total = dashes.length;

	const alertsResp = await alertsFetch;
	const alertsMap = await alertsResp.json();
	let alertTotal = 0;
	for (const folder in alertsMap) {
		alertTotal += alertsMap[folder].length;
	}
	console.info(`... found ${total} dashboards and ${alertTotal} alerts.`);

	for (const folder in alertsMap) {
		const alerts = alertsMap[folder];
		for (const alert of alerts) {
			const str = JSON.stringify(alert, null, 2);
			const m = str.match(rPattern);
			if (m) {
				const alertUrl = `${urlBase}/alerting/grafana/${alert.rules[0].grafana_alert.uid}/view`;
				console.log('Matched %s (%s / %s)', alertUrl, folder, alert.name);
				console.log(m);
			}
		}
	}


	let i = 0;
	function progress() {
		i++;
		if ((i % PROGRESS_CHUNK) === 0 || i === total) {
			console.info(`... checked dashboard ${i}/${total}...`);
		}
	}

	while (dashes.length) {
		// Batch the API queries in parallel to speed things up significantly.
		const dashBatch = dashes.splice(0, API_BATCH_SIZE);
		for (let dash of dashBatch) {
			progress();
			dash.fetch = fetch(urlDashApiBase + dash.uid);
		}

		// Wait for results
		await Promise.all(dashBatch.map(dash => dash.fetch));

		for (let dash of dashBatch) {
			const resp = await dash.fetch;
			const blob = await resp.text();
			const m = blob.match(rPattern);
			if (m) {
				console.log('Matched %s%s (%s)', urlBase, dash.url, dash.title);
				console.log(m);
			}
		}
	}

	console.info('Done!');
}

// Node.js usage
if (typeof process !== 'undefined' && !process.browser) {
	(async function main() {
		const path = await import('node:path');
		const pattern = process.argv[2];
		if (!pattern) {
			const cmd = path.basename(process.argv[0]);
			const base = path.basename(process.argv[1]);
			console.log(`usage: ${cmd} ./${base} "<pattern>"`);
			console.log('');
			console.log('pattern: Matched as regular expression against');
			console.log('         the raw dashboard JSON.');
			console.log('');
			console.log('Example:');
			console.log(`${cmd} ./${base} resourceloader_build`);
			console.log(`${cmd} ./${base} "mediawiki_(http|rate)"`);
			console.log('');
			process.exit(1);
		}
		await search(pattern);
	}()).catch( e => {
		console.log(e);
		process.exit(1);
	} );
}
