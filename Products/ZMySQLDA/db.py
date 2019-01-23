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
import logging
import time

from six.moves._thread import allocate_lock
from six.moves._thread import get_ident

from DateTime.DateTime import DateTime
from DateTime.interfaces import DateTimeError
from Shared.DC.ZRDB.TM import TM
import transaction
from ZODB.POSException import ConflictError
from ZODB.POSException import TransactionFailedError

try:
    import _mysql
    from _mysql_exceptions import NotSupportedError
    from _mysql_exceptions import OperationalError
    from _mysql_exceptions import ProgrammingError
except ImportError:  # mysqlclient > 1.4
    import MySQLdb as _mysql
    from MySQLdb import NotSupportedError
    from MySQLdb import OperationalError
    from MySQLdb import ProgrammingError
import MySQLdb
from MySQLdb.converters import conversions
from MySQLdb.constants import CLIENT
from MySQLdb.constants import CR
from MySQLdb.constants import ER
from MySQLdb.constants import FIELD_TYPE

LOG = logging.getLogger("ZMySQLDA")

hosed_connection = {
    CR.SERVER_GONE_ERROR: "Server gone.",
    CR.SERVER_LOST: "Server lost.",
    CR.COMMANDS_OUT_OF_SYNC: "Commands out of sync. Possibly a misplaced"
                             " semicolon (;) in a query."
}

query_syntax_error = (ER.BAD_FIELD_ERROR,)

key_types = {"PRI": "PRIMARY KEY", "MUL": "INDEX", "UNI": "UNIQUE"}

field_icons = "bin", "date", "datetime", "float", "int", "text", "time"

icon_xlate = {
    "varchar": "text",
    "char": "text",
    "enum": "what",
    "set": "what",
    "double": "float",
    "numeric": "float",
    "blob": "bin",
    "mediumblob": "bin",
    "longblob": "bin",
    "tinytext": "text",
    "mediumtext": "text",
    "longtext": "text",
    "timestamp": "datetime",
    "decimal": "float",
    "smallint": "int",
    "mediumint": "int",
    "bigint": "int",
}

type_xlate = {
    "double": "float",
    "numeric": "float",
    "decimal": "float",
    "smallint": "int",
    "mediumint": "int",
    "bigint": "int",
    "int": "int",
    "float": "float",
    "timestamp": "datetime",
    "datetime": "datetime",
    "time": "datetime",
}


def DateTime_or_None(s):
    try:
        return DateTime(s)
    except DateTimeError:
        return None


class DBPool(object):
    """
      This class is an interface to the database connection..
      Its caracteristic is that an instance of this class interfaces multiple
      instanes of db_cls class, each one being bound to a specific thread.
    """

    connected_timestamp = ""
    _create_db = False
    use_unicode = False
    charset = None

    def __init__(self, db_cls, create_db=False, use_unicode=False,
                 charset=None):
        """ Set transaction managed class for use in pool.
        """
        self._db_cls = db_cls
        # pool of one db object/thread
        self._db_pool = {}
        self._db_lock = allocate_lock()
        # auto-create db if not present on server
        self._create_db = create_db
        # unicode settings
        self.use_unicode = use_unicode
        self.charset = charset

    def __call__(self, connection):
        """ Parse the connection string.

            Initiate a trial connection with the database to check
            transactionality once instead of once per db_cls instance.

            Create database if option is enabled and database doesn't exist.
        """
        self.connection = connection
        db_flags = self._db_cls._parse_connection_string(connection,
                                                         self.use_unicode,
                                                         charset=self.charset)
        self._db_flags = db_flags

        # connect to server to determin tranasactional capabilities
        # can't use db_cls instance as it requires this information to work
        try:
            connection = MySQLdb.connect(**db_flags["kw_args"])
        except OperationalError:
            if self._create_db:
                kw_args = db_flags.get("kw_args", {}).copy()
                db = kw_args.pop("db", None)
                if not db:
                    raise
                connection = MySQLdb.connect(**kw_args)
                create_query = "create database %s" % db
                if self.use_unicode and not self.charset:
                    create_query += " default character set %s" % (
                                        self._db_cls.unicode_charset)
                elif self.charset:
                    create_query += " default character set %s" % self.charset
                connection.query(create_query)
                connection.store_result()
            else:
                raise
        transactional = connection.server_capabilities & CLIENT.TRANSACTIONS
        connection.close()

        # Some tweaks to transaction/locking db_flags based on server setup
        if db_flags["try_transactions"] == "-":
            transactional = False
        elif not transactional and db_flags["try_transactions"] == "+":
            raise NotSupportedError("transactions not supported by the server")
        db_flags["transactions"] = transactional
        del db_flags["try_transactions"]
        if transactional or db_flags["mysql_lock"]:
            db_flags["use_TM"] = True

        # will not be 100% accurate in regard to per thread connections
        # but as close as we're going to get it.
        self.connected_timestamp = DateTime()

        # return self as the database connection object
        # (assigned to _v_database_connection)
        return self

    def closeConnection(self):
        """ Close this threads connection. Used when DA is being reused
            but the connection string has changed. Need to close the db_cls
            instances and recreate to the new database. Only have to worry
            about this thread as when each thread hits the new connection
            string in the DA this method will be called.
        """
        ident = get_ident()
        try:
            self._pool_del(ident)
        except KeyError:
            pass

    def close(self):
        """ Used when manually closing the database. Resetting the pool
            dereferences the db_cls instances where they are then collected
            and closed.
        """
        self._db_pool = {}

    def _pool_set(self, key, value):
        """ Add a db to pool.
        """
        self._db_lock.acquire()
        try:
            self._db_pool[key] = value
        finally:
            self._db_lock.release()

    def _pool_get(self, key):
        """ Get db from pool. Read only, no lock necessary.
        """
        return self._db_pool.get(key)

    def _pool_del(self, key):
        """ Remove db from pool.
        """
        self._db_lock.acquire()
        try:
            del self._db_pool[key]
        finally:
            self._db_lock.release()

    def name(self):
        """ Return name of database connected to.
        """
        return self._db_flags["kw_args"]["db"]

    # Passthrough aliases for methods on db_cls class.
    def variables(self, *args, **kw):
        return self._access_db(method_id="variables", args=args, kw=kw)

    def tables(self, *args, **kw):
        return self._access_db(method_id="tables", args=args, kw=kw)

    def columns(self, *args, **kw):
        return self._access_db(method_id="columns", args=args, kw=kw)

    def query(self, *args, **kw):
        return self._access_db(method_id="query", args=args, kw=kw)

    def string_literal(self, *args, **kw):
        return self._access_db(method_id="string_literal", args=args, kw=kw)

    def unicode_literal(self, *args, **kw):
        try:
            return self._access_db(method_id="unicode_literal",
                                   args=args, kw=kw)
        except AttributeError:  # mysqlclient > 1.3.11
            # This is modeled after code in MySQLdb.connections.__init__
            new_args = (args[0].encode(self.charset or 'latin1'),) + args[1:]
            return self._access_db(method_id="string_literal",
                                   args=new_args, kw=kw)

    def _access_db(self, method_id, args, kw):
        """
          Generic method to call pooled objects' methods.
          When the current thread had never issued any call, create a db_cls
          instance.
        """
        ident = get_ident()
        db = self._pool_get(ident)
        if db is None:
            db = self._db_cls(**self._db_flags)
            self._pool_set(ident, db)
        return getattr(db, method_id)(*args, **kw)


class DB(TM):

    Database_Error = _mysql.Error

    defs = {
        FIELD_TYPE.CHAR: "i",
        FIELD_TYPE.DATE: "d",
        FIELD_TYPE.DATETIME: "d",
        FIELD_TYPE.DECIMAL: "n",
        FIELD_TYPE.NEWDECIMAL: "n",
        FIELD_TYPE.DOUBLE: "n",
        FIELD_TYPE.FLOAT: "n",
        FIELD_TYPE.INT24: "i",
        FIELD_TYPE.LONG: "i",
        FIELD_TYPE.LONGLONG: "l",
        FIELD_TYPE.SHORT: "i",
        FIELD_TYPE.TIMESTAMP: "d",
        FIELD_TYPE.TINY: "i",
        FIELD_TYPE.YEAR: "i",
    }

    conv = conversions.copy()
    conv[FIELD_TYPE.LONG] = int
    conv[FIELD_TYPE.DATETIME] = DateTime_or_None
    conv[FIELD_TYPE.DATE] = DateTime_or_None
    conv[FIELD_TYPE.DECIMAL] = float
    conv[FIELD_TYPE.NEWDECIMAL] = float
    del conv[FIELD_TYPE.TIME]

    _p_oid = _p_changed = None
    _sort_key = '1'
    _registered = False
    _finalize = False

    unicode_charset = "utf8"  # hardcoded for now

    def __init__(self, connection=None, kw_args=None, use_TM=None,
                 mysql_lock=None, transactions=None):
        self.connection = connection  # backwards compat
        self._kw_args = kw_args
        self._mysql_lock = mysql_lock
        self._use_TM = use_TM
        self._transactions = transactions
        self._forceReconnection()

    def close(self):
        """ Close connection and dereference.
        """
        if getattr(self, "db", None):
            self.db.close()
            self.db = None

    __del__ = close

    def _forceReconnection(self):
        """ (Re)Connect to database.
        """
        try:  # try to clean up first
            self.db.close()
        except Exception:
            pass
        self.db = MySQLdb.connect(**self._kw_args)
        # Newer mysqldb requires ping argument to attmept a reconnect.
        # This setting is persistent, so only needed once per connection.
        self.db.ping(True)

    @classmethod
    def _parse_connection_string(cls, connection, use_unicode=False,
                                 charset=None):
        """ Done as a class method to both allow access to class attribute
            conv (conversion) settings while allowing for wrapping pool class
            use of this method. The former is important to allow for subclasses
            to override the conv settings while the latter is important so
            the connection string doesn't have to be parsed for each instance
            in the pool.
        """
        kw_args = {"conv": cls.conv}
        flags = {"kw_args": kw_args, "connection": connection}
        kw_args["use_unicode"] = use_unicode
        if use_unicode:
            kw_args["charset"] = cls.unicode_charset
        if charset:
            kw_args["charset"] = charset
        items = connection.split()
        flags["use_TM"] = None
        if _mysql.get_client_info()[0] >= "5":
            kw_args["client_flag"] = CLIENT.MULTI_STATEMENTS
        if items:
            lockreq, items = items[0], items[1:]
            if lockreq[0] == "*":
                flags["mysql_lock"] = lockreq[1:]
                db_host, items = items[0], items[1:]
                flags["use_TM"] = True  # redundant. eliminate?
            else:
                flags["mysql_lock"] = None
                db_host = lockreq
            if "@" in db_host:
                db, host = db_host.split("@", 1)
                kw_args["db"] = db
                if ":" in host:
                    host, port = host.split(":", 1)
                    kw_args["port"] = int(port)
                kw_args["host"] = host
            else:
                kw_args["db"] = db_host
            if kw_args["db"] and kw_args["db"][0] in ("+", "-"):
                flags["try_transactions"] = kw_args["db"][0]
                kw_args["db"] = kw_args["db"][1:]
            else:
                flags["try_transactions"] = None
            if not kw_args["db"]:
                del kw_args["db"]
            if items:
                kw_args["user"], items = items[0], items[1:]
            if items:
                kw_args["passwd"], items = items[0], items[1:]
            if items:
                kw_args["unix_socket"], items = items[0], items[1:]

        return flags

    def tables(self, rdb=0, _care=("TABLE", "VIEW")):
        """ Returns list of tables.
        """
        t_list = []
        db_result = self._query("SHOW TABLE STATUS")
        for row in db_result.fetch_row(0):
            description = '%s, %s rows, character set/collation %s' % (
                            row[1], str(row[4]), row[14])
            t_list.append({'table_name': row[0],
                           'table_type': 'table',
                           'description': description})
        return t_list

    def columns(self, table_name):
        """ Returns list of column descriptions for ``table_name``.
        """
        c_list = []
        try:
            # Field, Type, Null, Key, Default, Extra
            db_result = self._query("SHOW COLUMNS FROM %s" % table_name)
        except ProgrammingError:
            # Table does not exist. Any other error should propagate.
            LOG.warning('columns query for non-existing table %s' % table_name)
            return ()

        for Field, Type, Null, Key, Default, Extra in db_result.fetch_row(0):
            info = {'name': Field,
                    'extra': (Extra,),
                    'nullable': (Null == b"YES") and 1 or 0}

            if Default is not None:
                info["default"] = Default
                field_default = b"DEFAULT '%s'" % Default
            else:
                field_default = b''

            if b"(" in Type:
                end = Type.rfind(b")")
                short_type, size = Type[:end].split(b"(", 1)
                if short_type not in (b"set", b"enum"):
                    if b"," in size:
                        info["scale"], info["precision"] = map(
                                int, size.split(b",", 1))
                    else:
                        info["scale"] = int(size)
            else:
                short_type = Type

            if short_type in field_icons:
                info["icon"] = short_type
            else:
                info["icon"] = icon_xlate.get(short_type, b"what")

            info["type"] = short_type
            nul = (Null == b'NO' and b'NOT NULL' or b'')
            info["description"] = b" ".join([Type,
                                             field_default,
                                             Extra or b"",
                                             key_types.get(Key, Key or b""),
                                             nul])
            if Key:
                info["index"] = True
                info["key"] = Key
            if Key == b"PRI":
                info["primary_key"] = True
                info["unique"] = True
            elif Key == b"UNI":
                info["unique"] = True

            c_list.append(info)

        return c_list

    def variables(self):
        """ Return dictionary of current mysql variable/values.
        """
        # variable_name, value
        variables = self._query("SHOW VARIABLES")
        return dict((name, value) for name, value in variables.fetch_row(0))

    def _query(self, query, force_reconnect=False):
        """
          Send a query to MySQL server.
          It reconnects automaticaly if needed and the following conditions are
          met:
           - It has not just tried to reconnect (ie, this function will not
             attempt to connect twice per call).
           - This conection is not transactionnal and has set no MySQL locks,
             because they are bound to the connection. This check can be
             overridden by passing force_reconnect with True value.
        """
        try:
            self.db.query(query)
        except OperationalError as exc:
            if exc.args[0] in query_syntax_error:
                raise OperationalError(exc.args[0],
                                       "%s: %s" % (exc.args[1], query))

            if not force_reconnect and \
               (self._mysql_lock or self._transactions) or \
               exc.args[0] not in hosed_connection:
                LOG.warning("query failed: %s" % (query,))
                raise

            # Hm. maybe the db is hosed.  Let's restart it.
            if exc.args[0] in hosed_connection:
                msg = "%s Forcing a reconnect." % hosed_connection[exc.args[0]]
                LOG.error(msg)
            self._forceReconnection()
            self.db.query(query)
        except ProgrammingError as exc:
            if exc.args[0] in hosed_connection:
                self._forceReconnection()
                msg = "%s Forcing a reconnect." % hosed_connection[exc.args[0]]
                LOG.error(msg)
            else:
                LOG.warning("query failed: %s" % (query,))
            raise

        return self.db.store_result()

    def query(self, sql_string, max_rows=1000):
        """ Execute ``sql_string`` and return at most ``max_rows``.
        """
        self._use_TM and self._register()
        desc = None
        rows = ()

        for qs in filter(None, [q.strip() for q in sql_string.split("\0")]):
            qtype = qs.split(None, 1)[0].upper()
            if qtype == "SELECT" and max_rows:
                qs = "%s LIMIT %d" % (qs, max_rows)
            db_results = self._query(qs)

            if desc is not None and \
               db_results and \
               db_results.describe() != desc:
                msg = "Multiple select schema are not allowed."
                raise ProgrammingError(msg)

            if db_results:
                desc = db_results.describe()
                rows = db_results.fetch_row(max_rows)
            else:
                desc = None

            if qtype == "CALL":
                # For stored procedures, skip the status result
                self.db.next_result()

        if desc is None:
            return (), ()

        items = []
        for info in desc:
            items.append({"name": info[0],
                          "type": self.defs.get(info[1], "t"),
                          "width": info[2],
                          "null": info[6]})

        return items, rows

    def string_literal(self, sql_str):
        """ Called from zope to quote/escape strings for inclusion
            in a query.
        """
        return self.db.string_literal(sql_str)

    def unicode_literal(self, sql_str):
        """ Similar to string_literal but encodes it first.
        """
        return self.db.unicode_literal(sql_str)

    # Zope 2-phase transaction handling methods

    def _register(self):
        """ Override to replace transaction register() call with join().

            The primary reason for this is to eliminate issues in both the
            super's _register() and transaction register(). The former has a
            bare except: that hides useful errors. The latter deals poorly with
            exceptions raised from the join due to state modifications made
            before the join attempt.

            They also both (for our purposes) needlessly add wrapper objects
            around self, resulting in unnecessary overhead.
        """
        if not self._registered:
            try:
                transaction.get().join(self)
            except TransactionFailedError:
                msg = "database connection failed to join transaction."
                LOG.error(msg)
            except ValueError:
                msg = "database connection failed to join transaction."
                LOG.error(msg, exc_info=True)
                raise
            else:
                self._begin()
                self._registered = True
                self._finalize = False

    def _begin(self, *ignored):
        """ Begin a transaction, if transactions are enabled.

        Also called from _register() upon first query.
        """
        try:
            self._transaction_begun = True
            self.db.ping()
            if self._transactions:
                self._query("BEGIN")
            if self._mysql_lock:
                self._query("SELECT GET_LOCK('%s',0)" % self._mysql_lock)
        except Exception:
            LOG.error("exception during _begin", exc_info=True)
            raise ConflictError

    def _finish(self, *ignored):
        """ Commit a transaction, if transactions are enabled and the
        Zope transaction has committed successfully.
        """
        if not self._transaction_begun:
            return
        self._transaction_begun = False
        try:
            if self._mysql_lock:
                self._query("SELECT RELEASE_LOCK('%s')" % self._mysql_lock)
            if self._transactions:
                self._query("COMMIT")
        except Exception:
            LOG.error("exception during _finish", exc_info=True)
            raise ConflictError

    def _abort(self, *ignored):
        """ Roll back the database transaction if the Zope transaction
        has been aborted, usually due to a transaction error.
        """
        if not self._transaction_begun:
            return
        self._transaction_begun = False
        if self._mysql_lock:
            self._query("SELECT RELEASE_LOCK('%s')" % self._mysql_lock)
        if self._transactions:
            self._query("ROLLBACK")
        else:
            LOG.error("aborting when non-transactional")

    def _mysql_version(self):
        """ Return mysql server version.
        """
        if getattr(self, "_version", None) is None:
            self._version = self.variables().get("version")
        return self._version

    def savepoint(self):
        """ Basic savepoint support.

            Raise AttributeErrors to trigger optimistic savepoint handling
            in zope's transaction code.
        """
        if self._mysql_version() < "5.0.2":
            # mysql supports savepoints in versions 5.0.3+
            LOG.warning("Savepoints unsupported with Mysql < 5.0.3")
            raise AttributeError

        if not self._transaction_begun:
            LOG.error("Savepoint used outside of transaction.")
            raise AttributeError

        return _SavePoint(self)


class _SavePoint(object):
    """ Simple savepoint object
    """

    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.ident = str(time.time()).replace(".", "sp")
        db_conn._query("SAVEPOINT %s" % self.ident)

    def rollback(self):
        self.db_conn._query("ROLLBACK TO %s" % self.ident)
