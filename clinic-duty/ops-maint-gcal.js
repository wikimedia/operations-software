/* eslint-disable no-console, no-implicit-globals, prefer-const */

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

	/* Assume the first capture group from start/end re will have the date we're looking for */
	static find( startRe, endRe, locationRe, message, tz = null ) {
		const startDateMatch = startRe.exec( message.text );
		if ( !startDateMatch ) {
			return null;
		}
		// Make Firefox happy with Date() input.
		// replace with global regex in place of replaceAll for node to work
		let startDateStr = startDateMatch[ 1 ].replace( /-/g, '/' );
		if ( tz !== null ) {
			startDateStr = startDateStr + ' ' + tz;
		}
		const startDate = Date.parse( startDateStr );

		const endDateMatch = endRe.exec( message.text );
		if ( !endDateMatch ) {
			return null;
		}

		let endDateStr = endDateMatch[ 1 ].replace( /-/g, '/' );
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
		const startDateRe = /^Start.*End\n([^(]*)/m;
		const endDateRe = /^Start.*End\n.*\t([^(]*)/m;
		const locationRe = /Location\(s\):\s*(.*)/;
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

class Telia {
	constructor( message ) {
		this.message = message;
	}

	static fromMessage( message ) {
		const re = /(Telia Carrier|Arelion)/;
		if ( !re.exec( message.text ) ) {
			return null;
		}
		return new Telia( message );
	}

	get work() {
		// XXX support more than one timespan/window
		const startDateRe = /^Service window start:(.*)$/m;
		const endDateRe = /^Service window end:(.*)$/m;
		const locationRe = /^Location:\s*(.*)$/m;
		return Work.find( startDateRe, endDateRe, locationRe, this.message );
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

/* Represent a maintenance message we have received. Within each message we're
 * looking for at least one "work" to do */
class Message {
	constructor( message, title = '-', url = '#' ) {
		this.message = message;
		this.textCache = null;
		this.title = title;
		this.url = url;
	}

	get inviteDetails() {
		// XXX replace with sth non-global
		return this.url + '\n\n' + this.text;
	}

	get text() {
		if ( this.textCache !== null ) {
			return this.textCache;
		}

		// join all html-blob text together
		const htmlBlobs = this.message.getElementsByTagName( 'html-blob' );
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
		let w;
		w = Telia.fromMessage( this );
		if ( w !== null ) {
			return w.work;
		}

		w = NTT.fromMessage( this );
		if ( w !== null ) {
			return w.work;
		}

		w = Lumen.fromMessage( this );
		if ( w !== null ) {
			return w.work;
		}

		w = Equinix.fromMessage( this );
		if ( w !== null ) {
			return w.work;
		}

		w = EuNetworks.fromMessage( this );
		if ( w !== null ) {
			return w.work;
		}

		console.log( '# Unable to find a parser for ' + this.text );
		return null;
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
