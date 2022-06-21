#!/bin/bash
#
# Simple script that will infinitely check for a change in the 's3r1al' metadata value
# via the '?wait_for_change=true' option. Once a change is discovered, it executes the
# command and sends STDOUT/STDERR to /dev/ttyS2 to view via the Google Compute 'serialPort'
# API. The 'startup-script' metadata will run this on reboot/reset as the 'root' user
# and will continue to run until the process is manually terminated or another reboot or
# reset occurs.
#
# Using /dev/ttyS2 is equivalant to 'serialPort?port=3' when using the API, which
# typically doesn't have anything sent to it. Ports 1 and 2 are used largely by syslog
# and kernel/boot messages. Using 'port=3' will exclusively be used for this use.
#

while true
do
   CMD=$(/usr/bin/curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/s3r1al?wait_for_change=true" -H "Metadata-Flavor: Google" 2>/dev/null)
   /bin/bash -c ${CMD} >> /dev/ttyS2
done
