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
import os

from App.ImageFile import ImageFile

from . import DA
from .permissions import add_zmysql_database_connections


def initialize(context):

    context.registerClass(
        DA.Connection,
        permission=add_zmysql_database_connections,
        constructors=(DA.manage_addZMySQLConnectionForm,
                      DA.manage_addZMySQLConnection),
        icon='www/da.gif')


misc_ = {}
for icon in ("table", "view", "stable", "what", "field", "text", "bin",
             "int", "float", "date", "time", "datetime",):
    misc_[icon] = ImageFile(os.path.join("www", "%s.gif") % icon, globals())
