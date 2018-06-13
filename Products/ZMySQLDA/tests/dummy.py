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
""" Dummy fixtures for testing
"""

RESULTS = {'show table status': [['table1', 'engine1', None, None, 5, None,
                                  None, None, None, None, None, None, None,
                                  None, 'my_collation']],
           'show variables': [('var1', 'val1'), ('version', '5.5.5')]}

TABLE = {'table_name': 'table1', 'table_type': 'type1', 'description': ''}

COLUMNS = [{'name': 'col1', 'icon': 'icon1', 'description': 'desc1'},
           {'name': 'col2', 'icon': 'icon2', 'description': 'desc2'}]


class FakeColumns(object):

    def __init__(self, table_name):
        self.cols = {table_name: COLUMNS}

    def columns(self, table_name):
        return self.cols[table_name]


class FakeResults:

    def __init__(self, results, **kw):
        self.results = results
        self.next_index = 0

    def fetch_row(self, count):
        return self.results


class FakeConnection:

    def __init__(self, **kw):
        self.server_capabilities = 0
        self.last_results = None
        self.last_query = None
        self.string_literal_called = False
        self.unicode_literal_called = False

        for k, v in kw.items():
            setattr(self, k, v)

    def ping(self, *args):
        pass

    def query(self, sql):
        self.last_query = sql
        sql = sql.lower()
        self.last_results = FakeResults(RESULTS.get(sql, []))
        return self.last_results

    _query = query

    def store_result(self):
        return self.last_results

    def close(self):
        pass

    def string_literal(self, txt):
        self.string_literal_called = txt

    def unicode_literal(self, txt):
        self.unicode_literal_called = txt
