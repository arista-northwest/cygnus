# CYGNUS

## Build

```
$ python setup.py bdist_rpm
```

## Deploy

On switch:

```
scp user[:password]@<host>:/path/to/Cygnus-<version>.noarch.rpm extension:
extension Cygnus-<version>.noarch.rpm
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
