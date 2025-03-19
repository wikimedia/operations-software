#!/usr/bin/node

/*
    Copyright (C) 2022 Wikimedia Foundation

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

// Browser usage, after pasting this file into the console (from a Grafana URL to avoid CSP errors):
//
//     search('wanobjectcache')
//     search('mediawiki_(http|rate)')
//     search('mediawiki_(http|rate)', { queries: true })
//     search('mediawiki_(http|rate)', { json: true })
//
// Node.js usage (Node 18 or higher is required):
//
//     $ node ./search-grafana-dashboards.js 'mediawiki_(http|rate)'
//     $ node ./search-grafana-dashboards.js 'mediawiki_(http|rate)' --queries
//     $ node ./search-grafana-dashboards.js 'mediawiki_(http|rate)' --json > results.json
//

/**
 * @param {string} pattern
 * @param {Object} [options]
 * @param {boolean} [options.queries=false]
 * @param {boolean} [options.json=false]
 */
async function search(pattern, options = {}) {
	const urlListQuery = 'https://grafana.wikimedia.org/api/search?query=&starred=false';
	const urlDashApiBase = 'https://grafana.wikimedia.org/api/dashboards/uid/';
	const urlBase = 'https://grafana.wikimedia.org';
	const urlAlertQuery = 'https://grafana.wikimedia.org/api/ruler/grafana/api/v1/rules?subtype=cortex';
	const API_BATCH_SIZE = 30;
	const PROGRESS_CHUNK = API_BATCH_SIZE;

	// Ease piping of results on the CLI:
	//
	// * send progress information to stderr instead of stdout.
	//   In the browser, avoid console.error as this shows in red, so use console.info instead.
	//   Note that in Node.js, console.info goes to stdout.
	//
	// * when using --json, print markdown summary to stderr.
	//
	const logError = console.error;
	const logProgress = (typeof process !== 'undefined' && !process.browser) ? console.error : console.info;
	const logSummary = options.json ? logProgress : console.log;
	const logJson = console.log;

	const rPattern = new RegExp('[^"\')}]*?' + pattern + '[^"\')}]*', 'g');
	logProgress('... internal regexp: ' + rPattern);

	// Output buffer
	const jsonSummary = {
		dashboards: [],
		alerts: [],
		totalDashboards: 0,
		totalAlerts: 0,
		pattern: pattern
	};
	let markdownSummary = '';

	// Start fetches in parallel, await later
	const listFetch = fetch(urlListQuery);
	const alertsFetch = fetch(urlAlertQuery);

	// Fetch dashboard list
	const listResp = await listFetch;
	const list = await listResp.json();
	const dashes = list.filter(item => item.type == 'dash-db');
	jsonSummary.totalDashboards = dashes.length;

	// Fetch alerts list (includes all alert contents)
	const alertsResp = await alertsFetch;
	const alertsMap = await alertsResp.json();
	let alertTotal = 0;
	for (const folder in alertsMap) {
		alertTotal += alertsMap[folder].length;
	}
	jsonSummary.totalAlerts = alertTotal;
	logProgress(`... fetched alerts ${alertTotal}/${alertTotal}`);

	// Match alert content
	for (const folder in alertsMap) {
		const alerts = alertsMap[folder];
		for (const alert of alerts) {
			const matches = JSON.stringify(alert, null, 2).match(rPattern);
			if (!matches) continue;

			const alertResult = {
				type: 'alert',
				url: `${urlBase}/alerting/grafana/${alert.rules[0].grafana_alert.uid}/view`,
				folder: folder,
				name: alert.name,
				matches: matches,
				queries: []
			};
			logProgress('... matched %s (%s / %s)', alertResult.url, alertResult.folder, alertResult.name);
			jsonSummary.alerts.push(alertResult);

			markdownSummary += `\n* Alert [${mdSanitizeLinkLabel(`${alertResult.folder} / ${alertResult.name}`)}](${alertResult.url})`;

			// Extract query expressions
			if (alert.rules?.[0]?.grafana_alert?.data) {
				for (const queryItem of alert.rules[0].grafana_alert.data) {
					const expr = queryItem.model?.expr || queryItem.model?.target;
					if (!expr || !expr.match(rPattern)) continue;
					alertResult.queries.push({
						type: 'prometheus',
						expr: expr,
						refId: queryItem.refId || 'Unknown'
					});
					markdownSummary += '\n  * Query: `' + mdSanitizeQueryExpr(expr) + '`'
				}
			}
		}
	}

	let i = 0;
	function progress() {
		i++;
		if ((i % PROGRESS_CHUNK) === 0 || i === jsonSummary.totalDashboards) {
			logProgress(`... fetched dashboard ${i}/${jsonSummary.totalDashboards}`);
		}
	}

	// Fetch dashboard content
	while (dashes.length) {
		// Each dashboard requires a separate API request to fetch its contents.
		//
		// Optimization: Start these fetches parallel to speed things up significantly.
		// But to order to avoid hitting rate limits, do it in batches.
		const dashBatch = dashes.splice(0, API_BATCH_SIZE);
		for (let dash of dashBatch) {
			progress();
			dash.fetch = fetch(urlDashApiBase + dash.uid);
		}

		// Wait for the batch to complete
		await Promise.all(dashBatch.map(dash => dash.fetch));

		// Match dashboard content
		for (let dash of dashBatch) {
			const resp = await dash.fetch;
			const blob = await resp.clone().text();
			let data;
			try {
				data = await resp.json();
			} catch (e) {
				logError('... failed to parse response from %s', urlDashApiBase + dash.uid);
				logError(e);
				continue;
			}
			const matches = blob.match(rPattern);
			if (!matches) continue;

			const dashResult = {
				type: 'dashboard',
				url: `${urlBase}${dash.url}`,
				title: dash.title,
				matches: matches,
				uid: dash.uid,
				panels: []
			};
			logProgress('... matched %s (%s)', dashResult.url, dashResult.title);
			jsonSummary.dashboards.push(dashResult);

			markdownSummary += `\n* Dashboard [${mdSanitizeLinkLabel(dashResult.title)}](${dashResult.url})`;

			// Flatten any nested panels in rows
			const panels = (data.dashboard?.panels || []).flatMap(
				(panel) => panel.panels ? [panel, ...panel.panels] : [panel]
			);

			for (const panel of panels) {
				const panelResult = matchPanel(panel, rPattern);
				if (!panelResult.queries.length) continue;

				dashResult.panels.push(panelResult);

				const panelUrl = `${dashResult.url}?viewPanel=${panelResult.id}`;
				markdownSummary += `\n  * Panel [${mdSanitizeLinkLabel(panelResult.title)}](${panelUrl})`;
				if (options.queries) {
					const listSeparator = `\n    * `;
					markdownSummary += listSeparator;
					markdownSummary += panelResult.queries.map(
						query => '`' + mdSanitizeQueryExpr(query.expr) + '`'
					).join(listSeparator);
				}
			}
		}
	}

	logSummary('\n## Summary\n');
	logSummary(`Searched for \`${pattern}\` and found ${jsonSummary.dashboards.length} matching dashboards and ${jsonSummary.alerts.length} matching alerts.`);
	logSummary(markdownSummary);

	if (options.json) {
		logJson(JSON.stringify(jsonSummary, null, 2));
	}

	// When used in the browser, `await search()` is preferred over `search(, {json: true})`
	// as the former allows you to interact with the object from the devtools console.
	return jsonSummary;
}

function mdSanitizeQueryExpr(text) {
	return text
		// Strip line breaks to avoid breaking markdown list item
		.replace(/[\n\s]+/g, ' ')
		// When showing results and helping the user understand how a metric is used,
		// the first 256 chars suffice. Trim anything longer, and add ellipsis (only if longer).
		.replace(/^(.{256}).+/, '$1…');
}

function mdSanitizeLinkLabel(text) {
	return text.replace(/[\[\]]/g, '');
}

/**
 * Get matching queries from one dashboard panel
 *
 * @param {Object} panel
 * @return {Object|null} Panel matches or null
 */
function matchPanel(panel, rPattern) {
	const queries = [];

	// Queries in timeseries, stat, etc.
	if (panel.targets) {
		for (const target of panel.targets) {
			// Prometheus uses 'expr', Graphite uses 'target'
			const expr = target.expr || target.target;
			if (!expr || !expr.match(rPattern)) continue;

			queries.push({
				type: target.datasource?.type || 'prometheus',
				expr: expr,
				refId: target.refId || 'Unknown'
			});
		}
	}

	return {
		id: panel.id,
		title: panel.title || 'Unnamed panel',
		type: panel.type,
		queries: queries
	};
}

// Node.js usage
if (typeof process !== 'undefined' && !process.browser) {
	(async function main() {
		const path = await import('node:path');
		const pattern = process.argv[2];

		let queries = false;
		let json = false;
		const optionArgs = process.argv.slice(3);
		while (optionArgs.length) {
			const option = optionArgs.shift();
			switch (option) {
				case '--queries':
					queries = true;
					break;
				case '-j':
				case '--json':
					json = true;
					break;
				default:
					console.error('Unknown option: ' + option);
					process.exit(1);
			}
		}

		if (!pattern) {
			const cmd = path.basename(process.argv[0]);
			const base = path.basename(process.argv[1]);
			console.log(`usage: ${cmd} ./${base} "<pattern>" [options]`);
			console.log('');
			console.log('pattern: Matched as regular expression against');
			console.log('         the raw dashboard JSON.');
			console.log('');
			console.log('options:');
			console.log('  --queries       Include a list of queries in the report');
			console.log('  --json, -j      Output results as JSON for further processing');
			console.log('');
			console.log('Example:');
			console.log(`${cmd} ./${base} resourceloader_build`);
			console.log(`${cmd} ./${base} "mediawiki_(http|rate)"`);
			console.log(`${cmd} ./${base} prometheus_query --json > results.json`);
			console.log('');
			process.exit(1);
		}

		await search(pattern, { queries, json });
	}()).catch( e => {
		console.error(e);
		process.exit(1);
	} );
}
