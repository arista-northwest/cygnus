#!/usr/bin/env python

from __future__ import print_function
import collections
# sigs = {
#     ""
# }

class BaseCommand(collections.Mapping):

    def __init__(self, line):

        self._line = line

        self._store = {}

    def __getitem__(self, item):
        return self._store[item]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def parse(self):
        tokens = self._line.split()


        action, type = tokens[:2]
        tokens = tokens[2:]

        print(action, type, tokens)

    # def parse(self, tokens):
    #
    #     args = {}
    #
    #     for i in range(0, len(tokens)-1):
    #         keyword = tokens[i]
    #         value = tokens[i+1])
    #         i += 2

# class NexthopGroup(BaseCommand):
#
#     def parse(self, tokens):
#         pass
#
# class Route(BaseCommand):
#
#     def parse(self, tokens):
#         pass

if __name__ == '__main__':
    commands = [
        "set nexthop-group name CYGNUS_NHG_1 entry 0 nexthop 172.16.130.1 label [ 30 31 32 ]",
        "set nexthop-group name CYGNUS_NHG_1 entry 1 nexthop 172.16.130.2 label [ 40 41 42 ]",
        "set route prefix 5.3.0.0/24 via CYGNUS_NHG_1",
        "del route prefix 5.3.0.0/24 via CYGNUS_NHG_1",
        "del route prefix 5.3.0.0/24",
        "del nexthop-group name CYGNUS_NHG_1"
    ]

    for c in commands:
        co = BaseCommand(c)
        co.parse()
