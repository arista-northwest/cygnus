# -*- coding: utf-8 -*-
# Copyright (c) 2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import socket
import eossdk

MAX_BUF_SIZE = 4096

class ServerHandler(eossdk.FdHandler):
    """Wrapper for FdHandler that accepts multiple client connetions on a TCP
    socket"""
    def __init__(self, sdk, address, backlog=5, vrf=None):

        # keep track fo client connections
        self._address = address
        self._backlog = backlog
        self._vrf = vrf
        self._connections = []
        self._server = None

        eossdk.FdHandler.__init__(self)
        self.acl_mgr = sdk.get_acl_mgr()
        self.vrf_mgr = sdk.get_vrf_mgr()

        #self.serve(address, backlog)

    def on_request(self, fd, data):
        """trigger when a request is received on a client connection.  users
        should override this method to handle the data"""
        pass

    def on_connection(self, fd, addr):
        pass

    def serve(self):

        self.tracer.trace0("Opening socket server on %s.%d" % self._address)

        if not self._vrf or self._vrf == "default":
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        else:
            self.tracer.trace0("vrf is set to %s" % self._vrf)
            fd = self.vrf_mgr.socket_at(socket.AF_INET, socket.SOCK_STREAM, 0, self._vrf)
            self._server = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM, 0)

        # reuse this socket if in TIME_WAIT state
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # set socket to non-blocking. Watch readble will let us know when data
        # is available
        self._server.setblocking(0)

        self._server.bind(self._address)
        self._server.listen(self._backlog)

        self.watch_readable(self._server.fileno(), True);

    def _is_connection_allowed(self, src_addr):
        """Test connection against configure service ACL

        Example:

        ip access-list standard MY_AGENT_ACL
            10 permit 192.168.0.0/16

        daemon MyAgent
            exec /path/to/myagent
            ip access-group MY_AGENT_ACL [in]
            no shutdown

        """

        src_ip, src_port = src_addr
        dst_ip, dst_port = self._server.getsockname()

        src_ip = eossdk.IpAddr(src_ip)
        dst_ip = eossdk.IpAddr(dst_ip)

        if not self.acl_mgr.stream_allowed(src_ip, dst_ip, 0, src_port,
                                           dst_port):
            return False

        return True

    def on_readable(self, fd):
        """React to events on watched sockets. This method handles both new
        connections and data received on existing ones"""

        if fd == self._server.fileno():
            new_fd, src_addr = self._server.accept()

            self.tracer.trace0("new connection from %s.%d" % src_addr)

            if not self._is_connection_allowed(src_addr):
                self.tracer.trace1(
                    "Connection from %s blocked by ACL" % src_addr[0])
                new_fd.close()
                return

            new_fd.setblocking(0)

            self._connections.append(new_fd)

            response = self.on_connection(new_fd, src_addr)

            if response:
                new_fd.send(response)

            self.watch_readable(new_fd.fileno(), True)
        else:
            readable = [f for f in self._connections if f.fileno() == fd][0]

            if not readable:
                return

            data = readable.recv(MAX_BUF_SIZE)

            if not data:
                self.tracer.trace0("closing connection on %d" % fd)
                self.watch_readable(fd, False)
                readable.shutdown(2)
                readable.close()
                self._connections.remove(readable)
                return

            self.tracer.trace0("new data on fd %d" % fd)
            response = self.on_request(readable, data)

            if response:
                readable.send(response)
