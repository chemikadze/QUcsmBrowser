#!/usr/bin/python

from pyucsm import UcsmError, UcsmFatalError, UcsmResponseError, UcsmObject

MOCK_UCS_TREES = {}

class MockConnection(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def login(self, login, password):
        self.login = login
        self.password = password
        try:
            self._mock_struct = MOCK_UCS_TREES[(self.host, self.port,
                                                self.login, self.password)]
        except KeyError:
            raise UcsmFatalError('Can not connect to host')

    def resolve_dn(self, dn, hierarchy=False):
        rns = dn.split('/')
        curr = self._mock_struct
        if rns == ['']:
            return curr
        try:
            for rn in rns:
                for child in curr.children:
                    if child.rn == rn:
                        curr = child
        except KeyError:
            return None
        res = curr.copy(dn)
        if not hierarchy:
            res.children = []
        return res

    def resolve_children(self, dn):
        obj = self.resolve_dn(dn, hierarchy=True)
        if obj:
            return obj.children
        else:
            return []