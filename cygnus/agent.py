#!/usr/bin/env python

"""
"""
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

    def __init__(self, sdk, address=("0.0.0.0", 6667), backlog=5, vrf="default"):
        self.tracer = eossdk.Tracer("Cygnus")

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

        if not re.search(r"\w+", data):
            return

        try:
            data = byteify(json.loads(data))
        except ValueError as exc:
            self.tracer.trace0("Data on is not valid JSON")
            fd.send("ERROR: Not valid JSON\n")
            return

        if "command" not in data:
            fd.send("ERROR: No command specified\n")
            return

        if "type" not in data:
            fd.send("ERROR: No type specified\n")
            return

        action = data["command"]
        type = re.sub(r"\-", "_", data["type"])
        params = {k:v for k,v in data.items() if k not in ["command", "type"]}

        func = getattr(self, "_%s_%s" % (action, type))

        func(**params)
