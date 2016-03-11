These are some crap scripts I steal pieces of in order
to do e.g. labs minons cleanup or get some random info
from the prod cluster.

Sticking them here so I can find them again, and because
they really aren't polished prod ready etc.

gather-minioninfo.sh is meant to be run on one's laptop.
The output from that can be shoved through parse-minion-output.py
Once you see what the problems are you can collect lists of
hosts and use salt-fixups.py on them; it's meant to be run
via ssh on the instances.

do_ssh_commands.py is meant to be able to tell me which hosts
are X or have X without having to log into a salt master,
oh and it's per cluster.  Some of the ssh tunnelling doesn't
work yet.  Whatevs.  What I really want it for is to copy
files around to various hosts. Didn't get that done either yet.
This also needs a variable for the ssh command from the laptop
e.g. I use a special script with a different name because it
manages user agents.
