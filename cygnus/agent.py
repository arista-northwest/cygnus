#!/usr/bin/env python

from __future__ import print_function
import json
import re
import sys
import time

import eossdk

import cygnus
from cygnus.server import ServerHandler
from cygnus.util import byteify

class CygnusAgent(eossdk.AgentHandler, ServerHandler):

    def __init__(self, sdk, address=("0.0.0.0", 50001), backlog=5, vrf="default"):
        self.tracer = eossdk.Tracer("Cygnus")

        self._buffer = None

        self.agent_mgr = sdk.get_agent_mgr()
        self.nhg_mgr = sdk.get_nexthop_group_mgr()
        self.ip_route_mgr = sdk.get_ip_route_mgr()

        eossdk.AgentHandler.__init__(self, self.agent_mgr)
        ServerHandler.__init__(self, sdk, address, backlog=backlog, vrf=vrf)

    def _set_nexthop_group(self, name, entries=[]):
        """
        {
            "command": "set",
            "type": "nexthop-group"
            "name": "CYGNUS_NHG_1",
            "entries": [
                {
                    "nexthop": "172.16.130.1",
                    "label": [30, 31, 32]
                },
                {
                    "nexthop": "172.16.130.2",
                    "label": [40, 41, 42]
                }
            ]
        }
        """
        nhg = eossdk.NexthopGroup(name, eossdk.NEXTHOP_GROUP_MPLS)

        for index, entry in enumerate(entries):
            labels = tuple([eossdk.MplsLabel(l) for l in entry["label"]])
            action = eossdk.NexthopGroupMplsAction(
                eossdk.MPLS_ACTION_PUSH,
                labels
            )
            nhe = eossdk.NexthopGroupEntry(eossdk.IpAddr(entry["nexthop"]))
            nhe.mpls_action_is(action)
            nhg.nexthop_set(index, nhe)

        self.nhg_mgr.nexthop_group_set(nhg)

    def _del_nexthop_group(self, name):
        """
        {
            "command": "del",
            "type": "nexthop-group"
            "name": "CYGNUS_NHG_1"
        }
        """
        is_active = self.nhg_mgr.active(name)

        if is_active:
            self.tracer.trace0("nexthop-group '%s' is still active" % name)
            return

        self.nhg_mgr.nexthop_group_del(name)

    def _set_route(self, prefix, nexthop_group):
        """
        {
            "command": "set",
            "type": "route",
            "prefix": "5.3.0.0/24",
            "nexthop_group": "CYGNUS_NHG_1"
        }
        """
        prefix = eossdk.IpPrefix(str(prefix))
        route_key = eossdk.IpRouteKey(prefix)
        route = eossdk.IpRoute(route_key)
        via = eossdk.IpRouteVia(route_key)
        via.nexthop_group_is(str(nexthop_group))

        self.ip_route_mgr.ip_route_set(route)
        self.ip_route_mgr.ip_route_via_set(via)

    def _del_route(self, prefix, nexthop_group=None):
        """
        {
            "command": "del",
            "type": "route",
            "prefix": "5.3.0.0/24",
            "nexthop_group": "CYGNUS_NHG_1" // optional
        }
        """
        prefix = eossdk.IpPrefix(str(prefix))
        route_key = eossdk.IpRouteKey(prefix)
        route = eossdk.IpRoute(route_key)

        if nexthop_group:
            via = eossdk.IpRouteVia(route_key)
            via.nexthop_group_is(str(nexthop_group))
            self.ip_route_mgr.ip_route_via_del(via)
        else:
            self.ip_route_mgr.ip_route_del(route_key)

    def on_agent_enabled(self, enabled):
        if enabled == False:
            self.tracer.trace0("shutting down now...")
            self.agent_mgr.agent_shutdown_complete_is(True)

    def on_initialized(self):
        self.tracer.trace0("cygnus agent initialized...")
        self.agent_mgr.status_set("version", cygnus.__version__)
        self.serve()

    def on_connection(self, fd, addr):
        fd.send("Hello %s, welcome to Cygnus.\n" % addr[0])

    def on_request(self, fd, data):

        #self.tracer.trace0("Got data %s" % data)

        if not re.search(r"\w+", data):
            return

        lines = data.splitlines(True)

        if self._buffer:
            lines[0] = self._buffer + lines[0]
            self._buffer = None

        if not re.search(r"[\r\n]+$", lines[-1]):
            self._buffer = lines.pop()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            try:
                self.tracer.trace0("Loading: %s" % line)
                loaded = byteify(json.loads(line))
            except ValueError as exc:
                self.tracer.trace0("Data on %d is not valid JSON" % fd.fileno())
                fd.send("ERROR: '%s' is not valid JSON\n" % line)
                continue

            if "command" not in loaded:
                fd.send("ERROR: No command specified\n")
                return

            if "type" not in loaded:
                fd.send("ERROR: No type specified\n")
                return

            action = loaded["command"]
            type = re.sub(r"\-", "_", loaded["type"])
            params = {k:v for k,v in loaded.items() if k not in ["command", "type"]}

            func = getattr(self, "_%s_%s" % (action, type))

            func(**params)
