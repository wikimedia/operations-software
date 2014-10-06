#!/bin/sh

cp /opt/otrs/Kernel/System/State.pm /opt/otrs/Kernel/System/State.pm.20140131
cp /opt/otrs/Kernel/Output/HTML/Layout.pm /opt/otrs/Kernel/Output/HTML/Layout.pm.20140131
cp /opt/otrs/Kernel/Modules/CustomerPreferences.pm /opt/otrs/Kernel/Modules/CustomerPreferences.pm.20140131
cp /opt/otrs/Kernel/Modules/CustomerTicketZoom.pm /opt/otrs/Kernel/Modules/CustomerTicketZoom.pm.20140131
cp /opt/otrs/Kernel/Modules/CustomerTicketMessage.pm /opt/otrs/Kernel/Modules/CustomerTicketMessage.pm.20140131
cp /opt/otrs/Kernel/Modules/CustomerTicketProcess.pm /opt/otrs/Kernel/Modules/CustomerTicketProcess.pm.20140131

cp ./Kernel/System/State.pm /opt/otrs/Kernel/System/State.pm
cp ./Kernel/Output/HTML/Layout.pm /opt/otrs/Kernel/Output/HTML/Layout.pm
cp ./Kernel/Modules/CustomerPreferences.pm /opt/otrs/Kernel/Modules/CustomerPreferences.pm
cp ./Kernel/Modules/CustomerTicketZoom.pm /opt/otrs/Kernel/Modules/CustomerTicketZoom.pm
cp ./Kernel/Modules/CustomerTicketMessage.pm /opt/otrs/Kernel/Modules/CustomerTicketMessage.pm
cp ./Kernel/Modules/CustomerTicketProcess.pm /opt/otrs/Kernel/Modules/CustomerTicketProcess.pm

chown otrs.www-data /opt/otrs/Kernel/System/State.pm /opt/otrs/Kernel/Output/HTML/Layout.pm /opt/otrs/Kernel/Modules/CustomerPreferences.pm /opt/otrs/Kernel/Modules/CustomerTicketZoom.pm /opt/otrs/Kernel/Modules/CustomerTicketMessage.pm /opt/otrs/Kernel/Modules/CustomerTicketProcess.pm 

chmod 664 /opt/otrs/Kernel/System/State.pm /opt/otrs/Kernel/Output/HTML/Layout.pm /opt/otrs/Kernel/Modules/CustomerPreferences.pm /opt/otrs/Kernel/Modules/CustomerTicketZoom.pm /opt/otrs/Kernel/Modules/CustomerTicketMessage.pm /opt/otrs/Kernel/Modules/CustomerTicketProcess.pm 

echo "remember to restart apache ok thanks bye"
