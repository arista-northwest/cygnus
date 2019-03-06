#!/bin/sh

AGENT=Cygnus
DEST=/usr/lib/SysdbMountProfiles/$AGENT
SOURCE="/usr/lib/SysdbMountProfiles/EosSdkAll"
TMP=/tmp/tmp_$AGENT
cat $SOURCE | sed "1s/agentName[ ]*:.*/agentName:${AGENT}-%sliceId/" > $TMP
delta=$(cmp /tmp/tmp_$AGENT $SOURCE)
if [ "$?" = "0" ]
then
  echo "Error: something is wrong"
  exit 1
else
  sudo mv $TMP $DEST
fi
