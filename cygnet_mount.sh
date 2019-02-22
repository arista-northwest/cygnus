bin=/mnt/flash/cygnet_agent
[ ${bin%.*} == $bin ] || echo "Error: remove dots from binary name"
name=$(basename $bin)
dest=/usr/lib/SysdbMountProfiles/$name
source="/usr/lib/SysdbMountProfiles/EosSdkAll"
cat $source | sed "1s/agentName[ ]*:.*/agentName:${name}-%sliceId/" > /tmp/tmp_$name
delta=$(cmp /tmp/tmp_$name $source)
if [ "$?" = "0" ]; then
  echo "Error: something is wrong"
else
  sudo mv /tmp/tmp_$name $dest
fi
