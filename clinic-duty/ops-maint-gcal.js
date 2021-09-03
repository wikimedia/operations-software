/* eslint-disable no-console, no-implicit-globals, prefer-const */

const CALENDAR_ID = 'd2lraW1lZGlhLm9yZ181OXJwOTczY243NmV2YWdzcmlxanMwZXV0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t';

// XXX add equinix and cyrusone

/**
 * Represent work to do.
 *
 * With start/end Date objects, work-specific details if applicable,
 * and the Message it is attached to
 */
class Work {
	constructor( start, end, details, message ) {
		this.start = start;
		this.end = end;
		this.details = details;
		this.message = message;
	}

	gcalendarLink( calendar, text ) {
		const startDateGcal = this.start.toISOString().replace( /-|:|\.\d\d\d/g, '' );
		const endDateGcal = this.end.toISOString().replace( /-|:|\.\d\d\d/g, '' );

		const link = document.createElement( 'a' );
		link.href = 'https://www.google.com/calendar/event?action=TEMPLATE';
		link.href += '&src=' + encodeURIComponent( calendar );
		link.href += '&text=' + encodeURIComponent( this.message.title );
		link.href += '&details=' + encodeURIComponent( this.message.inviteDetails );
		link.href += '&location=' + encodeURIComponent( this.details );
		link.href += '&dates=' + encodeURIComponent( startDateGcal ) + '/' + encodeURIComponent( endDateGcal );
		link.target = '_blank';
		link.textContent = text;
		return link;
	}

	/* Assume the first capture group from start/end re will have the date we're looking for */
	static find( startRe, endRe, locationRe, message ) {
		const startDateMatch = startRe.exec( message.text );
		if ( !startDateMatch ) {
			return null;
		}
		// Make Firefox happy with Date() input.
		// replace with global regex in place of replaceAll for node to work
		const startDate = new Date( startDateMatch[ 1 ].replace( /-/g, '/' ) );

		const endDateMatch = endRe.exec( message.text );
		if ( !endDateMatch ) {
			return null;
		}
		const endDate = new Date( endDateMatch[ 1 ].replace( /-/g, '/' ) );

		const locationMatch = locationRe.exec( message.text );
		let details = locationMatch ? locationMatch[ 1 ] : '';

		return [ new Work( startDate, endDate, details, message ) ];
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
		const re = /Telia Carrier/;
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

/* Represent a maintenance message we have received. Within each message we're
 * looking for at least one "work" to do */
class Message {
	constructor( message ) {
		this.message = message;
		this.textCache = null;
	}

	get title() {
		// XXX replace with sth non-global
		return document.querySelector( 'div[role=list]' ).attributes[ 'aria-label' ].textContent;
	}

	get inviteDetails() {
		// XXX replace with sth non-global
		return location.href + '\n\n' + this.text;
	}

	get text() {
		if ( this.textCache !== null ) {
			return this.textCache;
		}

		// join all html-blob innerText together
		const htmlBlobs = this.message.getElementsByTagName( 'html-blob' );
		if ( htmlBlobs.length < 1 ) {
			return null;
		}

		let res = '';
		for ( let i = 0, len = htmlBlobs.length; i < len; i++ ) {
			res += htmlBlobs[ i ].innerText + '\n';
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

		console.log( '# Unable to find a parser for ' + this.text );
		return null;
	}
}

/* exported addLinks */
function addLinks( verbose ) {
	const messages = document.querySelectorAll( 'section[role="listitem"]' );

	for ( let i = 0, len = messages.length; i < len; i++ ) {
		const msg = new Message( messages[ i ] );

		const work = msg.work;
		if ( work === null ) {
			console.log( 'No work found for ' + msg.text );
			continue;
		}

		if ( verbose ) {
			console.log( work );
		}

		let inviteLinks = [];
		work.forEach( function ( item, index ) {
			inviteLinks.push( item.gcalendarLink( CALENDAR_ID, 'work ' + ( index + 1 ) ) );
		} );

		let sender = messages[ i ].getElementsByTagName( 'h3' )[ 0 ];
		sender.append( '    Add to calendar: ' );
		inviteLinks.forEach( function ( item, index ) {
			sender.appendChild( item );
			if ( index < ( inviteLinks.length - 1 ) ) {
				sender.append( ' | ' );
			}
		} );
	}
}

/* global module */
if ( typeof module === 'object' && module.exports ) {
	module.exports = Message;
}
