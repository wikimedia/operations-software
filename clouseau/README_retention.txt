If your site is like most, it has a privacy policy, explicit or implicit,
stating how long what kinds of data may be kept.  This set of scripts and
the ccompanying library may be used to facilitate the auditing for such data
of log files, files in home directories, and files stashed in /root or
other locations where they may have been placed tempporarily and then forgotten.

The scripts rely on salt (saltstack.org); alternatively you can use your
own remote command execution mechanism and a set of wrapper scripts to run the
local audit functions directly on the hosts to be audited, collecting and
processing the output as you see fit.

These scripts assumes good faith on the part of the users of your systems;
someone determined to hide files with data can do so easily.  However, a user
intending to comply should get useful notifications from these scripts.
