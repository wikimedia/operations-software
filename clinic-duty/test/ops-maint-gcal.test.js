/* eslint-disable no-tabs */
'use strict';

const Message = require( '../ops-maint-gcal.js' );
const { test } = QUnit;

test( 'No parser found', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = 'unparseable text';
	assert.equal( msg.work, null );
} );

test( 'Telia single work', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Please note that Telia Carrier will perform maintenance work as outlined below.
Planned work reference:	...
Action and Reason:	...
Location:	Scottsville/VA, US

Service Window: PWICID primary	Work Status: Confirmed
Service window start:	2021-08-31 04:00 UTC
Service window end:	2021-08-31 12:00 UTC
Impacted Services
IC-ID	Wavelength Single Link	1 x 6 hours
`;
	assert.equal( msg.work.length, 1 );
	const work = msg.work[ 0 ];
	delete work.message;
	assert.equal( work.allday, false );
	assert.equal( work.details, 'Scottsville/VA, US' );
	assert.deepEqual( work.start, new Date( '2021-08-31T04:00:00.000Z' ) );
	assert.deepEqual( work.end, new Date( '2021-08-31T12:00:00.000Z' ) );
} );

test( 'Lumen', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Updates:

2021-08-24 14:16:03 GMT - This maintenance is scheduled.

Customer Impact:

ID


Start	End
2021-09-23 23:00 GMT (Greenwich Mean Time)	2021-09-24 05:00 GMT (Greenwich Mean Time)


Maintenance Location(s): BUDE, United Kingdom


Customer Name	Circuit ID	Alt Circuit ID	Bandwidth	A Location	Z Location	Impact Type	Maximum Duration	Order Number
XXX


Click here for assistance on this scheduled maintenance via Email.

Click here for immediate information on scheduled maintenances via the Lumen Customer Portal.

Click here to manage your notification subscriptions via the Lumen Portal.
`;
	assert.equal( msg.work.length, 1 );
	const work = msg.work[ 0 ];
	delete work.message;
	assert.equal( work.allday, false );
	assert.equal( work.details, 'BUDE, United Kingdom' );
	assert.deepEqual( work.start, new Date( '2021-09-23T23:00:00.000Z' ) );
	assert.deepEqual( work.end, new Date( '2021-09-24T05:00:00.000Z' ) );
} );

test( 'NTT', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Event Details

Ticket Number:
	GIN-ID

Start Date/Time:
	2021-09-01 07:00 UTC

End Date/Time:
	2021-09-01 10:00 UTC

Direct Impact:
	Users connected to this device will experience downtime during this maintenance window.


Reason:
	We will be performing an urgent hardware maintenance affecting the service(s) listed below.

Affected Services

Service ID	Service Type	IP Address	IPv6 Address	Device	Port ID	Market	Impact Level
stub description

Contact Information

NTT Global IP Network (AS2914)
Network Operations Center
Dallas, Texas, USA

	Email:noc@ntt.net
`;
	assert.equal( msg.work.length, 1 );
	const work = msg.work[ 0 ];
	delete work.message;
	assert.equal( work.allday, false );
	assert.equal( work.details, 'stub description' );
	assert.deepEqual( work.start, new Date( '2021-09-01T07:00:00.000Z' ) );
	assert.deepEqual( work.end, new Date( '2021-09-01T10:00:00.000Z' ) );
} );

test( 'Equinix single work single day', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Dear Equinix Customer,

DATE: 12-SEP-2021

SPAN: 12-SEP-2021 - 12-SEP-2021

LOCAL: SUNDAY, 12 SEP 01:00 - SUNDAY, 12 SEP 05:00
UTC: SATURDAY, 11 SEP 17:00 - SATURDAY, 11 SEP 21:00

IBX(s): SG1,SG2,SG3,SG4,SG5

DESCRIPTION:Please be advised that one of our upstream providers will be performing a software upgrade

There will be no impact to your services as traffic will be automatically rerouted to our alternate provider.
`;
	assert.equal( msg.work.length, 1 );
	const work = msg.work[ 0 ];
	delete work.message;
	assert.equal( work.allday, true );
	assert.equal( work.details, 'SG1,SG2,SG3,SG4,SG5' );
	assert.deepEqual( work.start, new Date( '2021-09-12T00:00:00.000Z' ) );
	assert.deepEqual( work.end, new Date( '2021-09-12T00:00:00.000Z' ) );
	/*
	const linkElement = work.gcalendarLink( 'calendar_id', 'link text' );
	const datesMatch = /dates=([^&]+)/.exec( linkElement.getAttribute('href') );
	assert.equal( datesMatch[ 1 ], '20210912/20210913' );
	*/
} );

test( 'Equinix multiple work multiple days', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Dear Equinix Customer,

DATE: 02-SEP-2021 - 06-SEP-2021

SPAN: 02-SEP-2021 - 06-SEP-2021

LOCAL: THURSDAY, 02 SEP 14:00 - FRIDAY, 03 SEP 06:00
UTC: THURSDAY, 02 SEP 19:00 - FRIDAY, 03 SEP 11:00

LOCAL: FRIDAY, 03 SEP 14:00 - SATURDAY, 04 SEP 06:00
UTC: FRIDAY, 03 SEP 19:00 - SATURDAY, 04 SEP 11:00

LOCAL: SATURDAY, 04 SEP 14:00 - SUNDAY, 05 SEP 06:00
UTC: SATURDAY, 04 SEP 19:00 - SUNDAY, 05 SEP 11:00

LOCAL: SUNDAY, 05 SEP 14:00 - MONDAY, 06 SEP 06:00
UTC: SUNDAY, 05 SEP 19:00 - MONDAY, 06 SEP 11:00

IBX: CH2

DESCRIPTION: Equinix engineering staff along with the UPS vendor will be performing corrective repairs on

The equipment being maintained supports your circuits indicated in the table.
`;
	assert.equal( msg.work.length, 1 );
	const work = msg.work[ 0 ];
	delete work.message;
	assert.equal( work.allday, true );
	assert.equal( work.details, 'CH2' );
	assert.deepEqual( work.start, new Date( '2021-09-02T00:00:00.000Z' ) );
	assert.deepEqual( work.end, new Date( '2021-09-06T00:00:00.000Z' ) );
	/*
	const linkElement = work.gcalendarLink( 'calendar_id', 'link text' );
	const datesMatch = /dates=([^&]+)/.exec( linkElement.getAttribute('href') );
	assert.equal( datesMatch[ 1 ], '20210902/20210906' );
	*/
} );
