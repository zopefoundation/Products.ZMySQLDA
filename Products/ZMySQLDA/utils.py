##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Utility classes and functions
"""

from Acquisition import Implicit
from App.special_dtml import HTMLFile
from ExtensionClass import Base


class BrowserBase(Base):
    def __getattr__(self, name):
        try:
            return self._d[name]
        except KeyError:
            raise AttributeError(name)


class values(object):
    def len(self):
        return 1

    def __getitem__(self, i):
        try:
            return self._d[i]
        except AttributeError:
            pass
        self._d = self._f()
        return self._d[i]


class TableBrowser(BrowserBase, Implicit):
    icon = "what"
    check = ""
    info = HTMLFile("www/table_info", globals())

    def tpValues(self):
        v = values()
        v._f = self.tpValues_
        return v

    def tpValues_(self):
        r = []
        tname = self._d["table_name"]
        for d in self._c.columns(tname):
            b = ColumnBrowser()
            b._d = d
            b.icon = d["icon"]
            b.table_name = tname
            r.append(b)
        return r

    def tpId(self):
        return self._d["table_name"]

    def tpURL(self):
        return "Table/%s" % self._d["table_name"]

    def name(self):
        return self._d["table_name"]

    def type(self):
        return self._d["table_type"]

    def description(self):
        return self._d["description"]


class ColumnBrowser(BrowserBase):
    icon = "field"

    def check(self):
        return '\t<input type="checkbox" name="%s.%s"/>' % (
            self.table_name,
            self._d["name"],
        )

    def tpId(self):
        return self._d["name"]

    def tpURL(self):
        return "Column/%s" % self._d["name"]

    def description(self):
        return self._d["description"]


table_icons = {"table": "table", "view": "view", "system_table": "stable"}
