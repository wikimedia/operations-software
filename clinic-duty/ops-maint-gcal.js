/* eslint-disable no-console, prefer-const */

const CALENDAR_ID = 'd2lraW1lZGlhLm9yZ181OXJwOTczY243NmV2YWdzcmlxanMwZXV0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t';

// XXX add cyrusone

/**
 * Represent work to do.
 *
 * With start/end Date objects, work-specific details if applicable,
 * and the Message it is attached to
 */
class Work {
	constructor( start, end, details, message, allday = false ) {
		this.start = start;
		this.end = end;
		this.details = details;
		this.message = message;
		this.allday = allday;
	}

	gcalendarLink( calendar ) {
		let startDateGcal = new Date( this.start ).toISOString().replace( /-|:|\.\d\d\d/g, '' );
		let endDateGcal = new Date( this.end ).toISOString().replace( /-|:|\.\d\d\d/g, '' );
		if ( this.allday ) {
			const startAllday = new Date( this.start );
			let endAllday = new Date( this.end );
			if ( this.end - this.start < 86400000 ) {
				// Same day, need to bump end date by one day to make gcal do the right thing
				endAllday.setDate( endAllday.getDate() + 1 );
			}

			// Leave out time for all day events
			startDateGcal = startAllday.toISOString().replace( /-|T.*/g, '' );
			endDateGcal = endAllday.toISOString().replace( /-|T.*/g, '' );
		}

		let href = 'https://www.google.com/calendar/event?action=TEMPLATE' +
			'&src=' + encodeURIComponent( calendar ) +
			'&text=' + encodeURIComponent( this.message.title ) +
			'&details=' + encodeURIComponent( this.message.inviteDetails ) +
			'&location=' + encodeURIComponent( this.details ) +
			'&dates=' + encodeURIComponent( startDateGcal ) + '/' + encodeURIComponent( endDateGcal );
		return href;
	}

	/* Assume the first capture group from start/end re will have the date we're looking for.
	 * If present, the second capture group will have the work' scheduled time.
	 */
	static find( startRe, endRe, locationRe, message, tz = null ) {
		const startDateMatch = startRe.exec( message.text );
		if ( !startDateMatch ) {
			return null;
		}
		// Make Firefox happy with Date() input.
		// replace with global regex in place of replaceAll for node to work
		let startDateStr = startDateMatch[ 1 ].replace( /-/g, '/' );
		if ( startDateMatch[ 2 ] ) {
			startDateStr = startDateStr + ' ' + startDateMatch[ 2 ];
		}
		if ( tz !== null ) {
			startDateStr = startDateStr + ' ' + tz;
		}
		const startDate = Date.parse( startDateStr );

		const endDateMatch = endRe.exec( message.text );
		if ( !endDateMatch ) {
			return null;
		}

		let endDateStr = endDateMatch[ 1 ].replace( /-/g, '/' );
		if ( endDateMatch[ 2 ] ) {
			endDateStr = endDateStr + ' ' + endDateMatch[ 2 ];
		}
		if ( tz !== null ) {
			endDateStr = endDateStr + ' ' + tz;
		}
		const endDate = Date.parse( endDateStr );

		const locationMatch = locationRe.exec( message.text );
		let details = locationMatch ? locationMatch[ 1 ] : '';

		return [ new Work( startDate, endDate, details, message ) ];
	}
}

class Equinix {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /Equinix Customer/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Equinix( message );
	}

	// XXX support multiple spans
	get work() {
		const startDateRe = /^SPAN:\s+(\S+)/m;
		const endDateRe = /^SPAN:\s+\S+\s+-\s+(\S+)/m;
		const locationRe = /^IBX(?:\(s\))?:\s+(\S+)/m;
		const w = Work.find( startDateRe, endDateRe, locationRe, this.message, 'UTC' );
		// No start/end time in spans, thus set work as all day
		w.forEach( function ( item ) {
			item.allday = true;
		} );
		return w;
	}
}

class Lumen {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /Lumen Customer Portal/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Lumen( message );
	}

	get work() {
		const startDateRe = /StartEnd([^(]+)/;
		const endDateRe = /StartEnd.*?\)([^(]+)/;
		const locationRe = /Location\(s\):\s*(.*)Customer/;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
	}
}

class NTT {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /noc@ntt.net/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new NTT( message );
	}

	get work() {
		const startDateRe = /^Start Date\/Time:\n(.*)/m;
		const endDateRe = /^End Date\/Time:\n(.*)$/m;
		const locationRe = /^Affected Services\n\n.*\n(.*)/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
	}
}

class Arelion {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /Arelion/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Arelion( message );
	}

	get work() {
		// XXX support more than one timespan/window
		const startDateRe = /Service window start:\s+(.+)\n/m;
		const endDateRe = /Service window end:\s+(.+)\n/m;
		const locationRe = /Location:\s+(\S+)/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
	}
}

class Orange {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /Orange customer/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Orange( message );
	}

	get work() {
		const startDateRe = /Beginning:\s*(.*?) at (.*?)\s*$/m;
		const endDateRe = /End:\s*(.*?) at (.*?)\s*$/m;
		const locationRe = /Impact:\s*(.*?)\s*$/m; // Not exact but location isn't available
		return Work.find( startDateRe, endDateRe, locationRe, this.message, 'UTC' );
	}
}

class Telxius {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /@telxius\.com/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Telxius( message );
	}

	get work() {
		const startDateRe = /SCHEDULE.*:\n(.+) - /m;
		const endDateRe = /SCHEDULE.*:\n.+ - (.+)/m;
		const locationRe = /LOCATION.*: (.+)/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message, 'UTC' );
	}
}

class EuNetworks {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /euNetworks Change/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new EuNetworks( message );
	}

	get work() {
		const startDateRe = /Start Time:\s+(.*)$/m;
		const endDateRe = /End Time:\s+(.*)$/m;
		const locationRe = /^Location Description:\s*(.*)$/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
	}
}

class SGIX {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /@sgix.sg/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new SGIX( message );
	}

	get work() {
		const startDateRe = /Start Time:\s+(.+?) at (.+?) hrs/m;
		const endDateRe = /End Time:\s+(.+?) at (.+?) hrs/m;
		const locationRe = /(SG[0-9]+)/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message, 'GMT+8' );
	}
}

class DECIX {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /support@de-cix.net/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new DECIX( message );
	}

	get work() {
		const startDateRe = /Work start:\s+(.*)$/m;
		const endDateRe = /Work end:\s+(.*)$/m;
		const locationRe = /Devices: (.*)/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
	}
}

class DigitalRealty {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /ecc@digitalrealty.com/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new DigitalRealty( message );
	}

	get work() {
		const startDateRe = /Time Start:\s+(.+?) Local time/m;
		const endDateRe = /Time End:\s+(.+?) Local time/m;
		const locationRe = /Site Location\s*: (.+?)Impact/m;
		// XXX not necessarily accurate depending on daylight savings or the actual location
		return Work.find( startDateRe, endDateRe, locationRe, this.message, 'GMT+2' );
	}
}

/**
 * Represent a maintenance message we have received.
 *
 * Within each message, we're looking for at least one "work" to do.
 */
class Message {
	constructor( message, title = '-', url = '#' ) {
		this.message = message;
		this.textCache = null;
		this.title = title;
		this.url = url;
	}

	get inviteDetails() {
		return this.url + '\n\n' + this.text;
	}

	get text() {
		if ( this.textCache !== null ) {
			return this.textCache;
		}

		// fetch elements with the message's content
		const htmlBlobs = this.message.querySelectorAll( '[role="region"]' );
		if ( htmlBlobs.length < 1 ) {
			return null;
		}

		let res = '';
		for ( let i = 0; i < htmlBlobs.length; i++ ) {
			res += htmlBlobs[ i ].textContent + '\n';
		}

		this.textCache = res;
		return this.textCache;
	}

	get work() {
		let w = (
			Arelion.fromMessage( this ) ||
			NTT.fromMessage( this ) ||
			Lumen.fromMessage( this ) ||
			Equinix.fromMessage( this ) ||
			EuNetworks.fromMessage( this ) ||
			Orange.fromMessage( this ) ||
			Telxius.fromMessage( this ) ||
			SGIX.fromMessage( this ) ||
			DECIX.fromMessage( this ) ||
			DigitalRealty.fromMessage( this )
		);

		if ( w !== null ) {
			return w.work;
		} else {
			console.log( '# Unable to find a parser for ' + this.text );
			return null;
		}
	}
}

/* exported addLinks */
function addLinks( verbose ) {
	const messages = document.querySelectorAll( 'section[role="listitem"]' );
	const title = document.querySelector( 'div[role=list]' ).getAttribute( 'aria-label' );
	const url = location.href;

	for ( let i = 0, len = messages.length; i < len; i++ ) {
		const msg = new Message( messages[ i ], title, url );

		const work = msg.work;
		if ( work === null ) {
			console.log( 'No work found for ' + msg.text );
			continue;
		}

		if ( verbose ) {
			console.log( work );
		}

		let sender = messages[ i ].querySelector( 'h3' );
		sender.append( '    Add to calendar: ' );
		work.forEach( ( item, index ) => {
			const link = document.createElement( 'a' );
			link.href = item.gcalendarLink( CALENDAR_ID );
			link.target = '_blank';
			link.textContent = 'work ' + ( index + 1 );

			sender.appendChild( link );

			if ( index < ( work.length - 1 ) ) {
				sender.append( ' | ' );
			}
		} );
	}
}

/* global module */
if ( typeof module === 'object' && module.exports ) {
	module.exports = Message;
}
