What this is:
  This script produces lists of hosts with various features,
  e.g. 'have dns entries', 'have puppet certs but are not
  known to salt', etc.

Why use it:
  A couple of us use it to check that hosts are properly
  decommissioned, to check puppet run statuses, and other
  similar things.  This helps us keep our puppet and other
  manifests clean and in sync.

To run:
  This script must be run from a salt master.

  python check-hosts.py --help
    will give you a short usage message

  python check-hosts.py --extendedhelp
    will give you a ginormous one.

Warnings:
  Sometimes salt commands fail without detection.  If you see a
  message 'failed to get/retrieve/find' something-or-other, try
  again.
  Some reports, namely logpuppet and salt, are expensive because
  they require running a command on all clients.
  Logpuppet cannot check puppet status on hosts not known to salt.
  Dns checks are for A records only, no IPV6, and absolutely no
  CNAME and no plans for it.

Bugs:
  Lots and lots, waiting to be discovered.

