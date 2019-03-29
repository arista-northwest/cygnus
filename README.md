# CYGNUS

## Build

```
git clone https://github.com/arista-northwest/cygnus.git
cd cygnus
docker build -t rpmbuild https://github.com/arista-northwest/docker-rpmbuild.git
docker run --rm -it -v $(pwd):/project rpmbuild python setup.py bdist_rpm
```

## Deploy

```
scp dist/Cygnus-<version>.noarch.rpm admin@yo630:/mnt/flash/Cygnus-latest.rpm
# delete old extension if needed and be sure to shutdown the agent before
# upgrading
no extension Cygnus-latest.rpm
copy flash:Cygnus-latest.rpm extension:
extension Cygnus-latest.rpm
copy installed-extensions boot-extensions

configure
!
ip access-list standard CYGNUS_ACL
   10 permit any
!
daemon Cygnus
   exec /usr/bin/Cygnus [--address ADDRESS] [--port PORT] [--vrf VRF] [--backlog BACKLOG]
   ip access-group CYGNUS_ACL
   no shutdown

trace Cygnus-Cygnus setting Cygnus/*
```

### Connecting.

```
$ telnet yo630 50001
Trying 172.24.70.162...
Connected to yo630.sjc.aristanetworks.com.
Escape character is '^]'.
Hello 10.95.79.114, welcome to Cygnus.
```

### Example commands ():

```
{ "command": "set", "type": "nexthop-group", "name": "CYGNUS_TEST_1", "entries": [ { "nexthop": "169.254.0.33", "label": [1000] } ]}
{ "command": "set", "type": "route", "prefix": "200.0.0.0/24", "nexthop_group": "CYGNUS_TEST_1" }
{ "command": "del", "type": "route", "prefix": "200.0.0.0/24", "nexthop_group": "CYGNUS_TEST_1" }
{ "command": "del", "type": "route", "prefix": "200.0.0.0/24" }
{ "command": "del", "type": "nexthop-group", "name": "CYGNUS_TEST_1" }
```

### Scripting example commands, example selects only 'set' commands:

```
cat examples/nhg.json | grep set | ncat yo630 50001
```
