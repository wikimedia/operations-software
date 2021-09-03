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
	assert.propEqual( work, {
		details: 'Scottsville/VA, US',
		end: new Date( '2021-08-31T12:00:00.000Z' ),
		start: new Date( '2021-08-31T04:00:00.000Z' )
	} );
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
	assert.propEqual( work, {
		details: 'BUDE, United Kingdom',
		end: new Date( '2021-09-24T05:00:00.000Z' ),
		start: new Date( '2021-09-23T23:00:00.000Z' )
	} );
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
	assert.propEqual( work, {
		details: 'stub description',
		end: new Date( '2021-09-01T10:00:00.000Z' ),
		start: new Date( '2021-09-01T07:00:00.000Z' )
	} );
} );
