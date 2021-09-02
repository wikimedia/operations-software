const CALENDAR_ID = 'd2lraW1lZGlhLm9yZ181OXJwOTczY243NmV2YWdzcmlxanMwZXV0OEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t';

// XXX add equinix and cyrusone

/* Represent a maintenance message we have received. Within each message we're
 * looking for at least one "work" to do */
class Message {
    constructor(message) {
        this.message = message
    }

    get title() {
        // XXX replace with sth non-global
        return document.querySelector("div[role=list]").attributes['aria-label'].textContent
    }

    get invite_details() {
        // XXX replace with sth non-global
        return location + "\n\n" + this.text
    }

    get text() {
        if (this._text != null) {
            return this._text
        }

        /* join all html-blob innerText together */
        var htmlBlobs = this.message.getElementsByTagName("html-blob")
        if (htmlBlobs.length < 1) {
            return null
        }

        var res = ""
        for (var i = 0, len = htmlBlobs.length; i < len; i++) {
            res += htmlBlobs[i].innerText + "\n"
        }

        this._text = res
        return this._text
    }

    get work() {
        var w = Telia.FromMessage(this)
        if (w != null) {
            return w.work
        }

        var w = NTT.FromMessage(this)
        if (w != null) {
            return w.work
        }

        var w = Lumen.FromMessage(this)
        if (w != null) {
            return w.work
        }

        console.log("Unable to find a parser for " + this.text)
        return null
    }
}


/* Represent work to do, with start/end Date objects, work-specific details if
 * applicable and the Message it is attached to */
class Work {
    constructor(start, end, details, message) {
        this.start = start
        this.end = end
        this.details = details
        this.message = message
    }

    gcalendar_link(calendar, text) {
        var start_date_gcal = this.start.toISOString().replace(/-|:|\.\d\d\d/g, '');
        var end_date_gcal = this.end.toISOString().replace(/-|:|\.\d\d\d/g, '');

        var link = document.createElement('a');
        link.href = 'https://www.google.com/calendar/event?action=TEMPLATE';
        link.href += '&src=' + encodeURIComponent(calendar);
        link.href += '&text=' + encodeURIComponent(this.message.title);
        link.href += '&details=' + encodeURIComponent(this.message.invite_details);
        link.href += '&location=' + encodeURIComponent(this.details);
        link.href += '&dates=' + encodeURIComponent(start_date_gcal) + '/' + encodeURIComponent(end_date_gcal);
        link.target = '_blank';
        link.innerHTML = text;
        return link;
    }

    /* Assume the first capture group from start/end re will have the date we're looking for */
    static find(start_re, end_re, location_re, message) {
        var start_date_match = start_re.exec(message.text);
        if (!start_date_match) {
            return null
        }
        // Make Firefox happy with Date() input.
        // replace with global regex in place of replaceAll for node to work
        var start_date = new Date(start_date_match[1].replace(/-/g, '/'));

        var end_date_match = end_re.exec(message.text);
        if (!end_date_match) {
            return null
        }
        var end_date = new Date(end_date_match[1].replace(/-/g, '/'));

        var location_match = location_re.exec(message.text);
        if (location_match) {
            var location = location_match[1];
        } else {
            var location = "";
        }

        return [new Work(start_date, end_date, location, message)]
    }
}


class Lumen {
    constructor(message) {
        this.message = message
    }

    static FromMessage(message) {
        var re = /Lumen Customer Portal/
        if (!re.exec(message.text)) {
            return null
        }
        return new Lumen(message)
    }

    get work() {
        var start_date_re = /^Start.*End\n([^(]*)/m;
        var end_date_re = /^Start.*End\n.*\t([^(]*)/m;
        var location_re = /Location\(s\):\s*(.*)/;

        return Work.find(start_date_re, end_date_re, location_re, this.message)
    }
}

class NTT {
    constructor(message) {
        this.message = message
    }

    static FromMessage(message) {
        var re = /noc@ntt.net/
        if (!re.exec(message.text)) {
            return null
        }
        return new NTT(message)
    }

    get work() {
        var start_date_re = /^Start Date\/Time:\n(.*)/m;
        var end_date_re = /^End Date\/Time:\n(.*)$/m;
        var location_re = /^Affected Services\n\n.*\n(.*)/m;

        return Work.find(start_date_re, end_date_re, location_re, this.message)
    }
}

class Telia {
    constructor(message) {
        this.message = message
    }

    static FromMessage(message) {
        var re = /Telia Carrier/
        if (!re.exec(message.text)) {
            return null
        }
        return new Telia(message)
    }

    get work() {
        // XXX support more than one timespan/window
        var start_date_re = /^Service window start:(.*)$/m;
        var end_date_re = /^Service window end:(.*)$/m;
        var location_re = /^Location:\s*(.*)$/m;

        return Work.find(start_date_re, end_date_re, location_re, this.message)
    }
}


function addLinks(verbose) {
    var messages = document.querySelectorAll("section[role=listitem]")

    for (var i = 0, len = messages.length; i < len; i++) {
        var msg = new Message(messages[i])

        var work = msg.work
        if (work == null) {
            console.log("No work found for " + msg.text)
            continue
        }

        if (verbose) {
            console.log(work)
        }

        var inviteLinks = []
        work.forEach(function (item, index) {
            inviteLinks.push(item.gcalendar_link(CALENDAR_ID, 'work ' + (index + 1)))
        });

        var sender = messages[i].getElementsByTagName('h3')[0]
        sender.append("    Add to calendar: ")
        inviteLinks.forEach(function (item, index) {
            sender.appendChild(item)
            if (index < (inviteLinks.length - 1)) {
                sender.append(" | ")
            }
        })
    }
}

module.exports = Message