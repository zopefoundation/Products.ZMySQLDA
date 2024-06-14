Products.ZMySQLDA change log
============================

5.1 (unreleased)
----------------


- Add support for Python 3.12.

- Drop support for Python 3.7.

5.0 (2023-02-02)
----------------

- Drop support for Python 2.7, 3.5, 3.6.

- Drop support for Zope 2 and Zope 4.

- Drop support for ``mysqlclient < 1.4``.


4.11 (2022-12-16)
-----------------

- Fix insidious buildout configuration bug for tests against Zope 4.

- Add support for Python 3.10 and 3.11.


4.10 (2021-03-30)
-----------------

- Move the project to the zopefoundation GitHub organization.


4.9 (2021-03-29)
----------------

- Add support for Python 3.9 and Zope 5


4.8 (2020-07-13)
----------------
- ZMI refresh for Zope 4 with svg icons
  (`#20 <https://github.com/zopefoundation/Products.ZMySQLDA/pull/20>`_)


4.7 (2020-05-04)
----------------
- truncate failed query logging if the query is too long
  (`#19 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/19>`_)


4.6 (2020-03-03)
----------------
- removed error-prone server version check for savepoint support
  (`#18 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/18>`_)

- added additional unit tests for SQL quoting


4.5 (2019-10-13)
----------------
- rely on the Zope 4 branch for tests so we don't lose Python 2 compatibility

- combine Status and Properties ZMI tabs to improve usability


4.4 (2019-06-17)
----------------
- add timeout parameter for DatabaseAdapter and database pool classes

- add timeout parameter to Add and Edit Forms

- make sure timeout is None or int
  (`#10 <https://github.com/zopefoundation/Products.ZMySQLDA/pull/10/files>`_)


4.3 (2019-05-28)
----------------
- make sure SQL quoting an unencoded string does not change the string type


4.2 (2019-05-21)
----------------
- fix wrong use of ``charset`` for ``unicode_literal``


4.1 (2019-04-26)
----------------
- fix the Browse tab under Python 3
  (`#14 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/14>`_)

- add more content to the long_description metadata
  (`#13 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/13>`_)

- fixes to the Browse ZMI tab


4.0 (2019-03-31)
----------------
- fix database version detection for savepoint support
  (`#7 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/7>`_)

- remove explicit ``setuptools`` version pin in ``setup.py``
  (`#11 <https://github.com/zopefoundation/Products.ZMySQLDA/issues/11>`_)

- more strict flake8 code style compliance

- trove classifier cleanup

- buildout configuration cleanup


4.0b5 (2019-02-20)
------------------
- When editing a connection in the ZMI, show an error message and not
  an exception when the connection fails.

- ZMI usability enhanced by providing feedback when editing a connection

- Specify supported Python versions using ``python_requires`` in setup.py

- Added support for Python 3.8


4.0b4 (2019-01-24)
------------------
- additional compatibility fixes for mysqlclient 14.0 and up


4.0b3 (2019-01-22)
------------------
- compatibility fix for mysqlclient 14.0 and up


4.0b2 (2018-12-11)
------------------
- added the ability to set the MySQL connection character set
  separate from the unicode flag.

- make the checkboxes on the add view work correctly

- declare (and test for) Python 3.7 compatibility

- make the checkboxes on the `Properties` ZMI tab work

- added missing ``six`` dependency declaration

- add some functional tests that require a running database server,
  see the documentation for how to set it up.


4.0b1 (2018-06-11)
------------------
- New maintainers: SNTL PUBLISHING / HOFFMANN+LIEBENBERG GMBH and
  Jens Vagelpohl

- Moved away from the unsupported ``MySQLdb1`` to the fork
  ``mysqlclient``, which is Python 3-compatible.

- Added simple buildout configuration with tox integration

- Zope 4 and Python 3 compatibility

- Added unit tests

- Added some ``Sphinx``-based documentation and copied any useful
  items from the old ``HelpSys`` files.

- Removed the hurt system files.

- Improved the ``Browse`` tab with more table information.


3.1.1
-----
- #3106015: zope 2.12/plone4 compatibility fix (thanks Mark Van den Borre)

- #3076433: column descriptions always said NOT NULL (thanks Frank Hoffmann)


3.1
---
- #2357223: Savepoint support


3.0
---
- Added ``Setuptools`` support to create an egg package thanks to
  Brett Carter.

- Added condition to handle connection getting "out of sync". This can occur
  when, for instance, you get a stray semicolon in a query. When a connection
  gets in this state it is hosed and must be closed and reconnected.

- Made some changes to how ``use_unicode`` and ``auto_create_db`` are set to
  better allow for subclassing and extensions of the base classes.

- Added handling of NEWDECIMAL which was added for mysql 5.0.

- Added basic support for procedure calls using ``CALL`` query.


3.0beta1
--------
- Fixed issue with ``sql_quote__`` getting called prior to connection being made.

- Fixed bug #1916952. Updating to API change in MySQLdb 1.2.2 ping method.

- Fixed backwards compatibility issue with MySQLdb versions <= 1.2.1.


3.0alpha4
---------
- Fixed pernicious corner case bug with joining a transaction after the
  transaction has started and been aborted.

- Zope dependency raised to Zope-2.8 or newer.


3.0alpha3
---------
- Unicode support now works!

- Unicode support reworked to use MySQLdb's unicode support instead of its
  own half-baked layer.

- Minor cleanups and extensions to database introspection methods.

- Minor cleanups/fixes to dtml.

- Removed a few unnecessary thread locks.

- Changed failed query logging entries from errors to warnings.


3.0alpha2
---------
- Moved DBPool instantiation from factory() to connect() to better facilitate
  API backwards compatibility.

- Changed all default values on keyword arguments for the auto create db
  feature. They all now default to True.

- Left in a bit of debugging code that disabled the new create_db
  functionality. Removed it.


3.0alpha1
---------
- New maintainer: John Eikenberry

- Note that there are some changes in the internal API. So if you have
  subclassed you should double check compatibility.

Features:
~~~~~~~~~
- Experimental Unicode support has been added. It is hardcoded to UTF-8 and
  has had limited testing at this point. Adapted from patches made by Graeme
  Mathieson.

- New optional feature of automatically creating the database provided in the
  connection string. The mysql ``user`` used for the connection must have
  CREATE permission. It defaults to on to encourage more testing.

- Database connection not created until first use instead of when the
  object is first loaded. Ie. connection created at ``connect()`` call instead
  of ``__setstate__()`` call. This helps conserve system resources and makes
  debugging connection issues a bit easier. It is also needed for the new
  db pool implementation (see below).

Bugs:
~~~~~
- Automatically reopens connections closed by client timeouts.

- Fixed major deadlock causing bug that can occur with versions of Zope
  greater than 2.8. It was caused by the use of the volatile attribute
  ``_v_`` to keep the reference to the existing connection. Volatile
  attributes can go away mid-transaction which would cause a deadlock when
  used with a transactional engine (eg. innodb). The fix involves a fixed
  pool of adapters and db connections. This also allowed for the elimination
  of many of the locks. Adapted from patches made by Vincent Pelletier.

- #670137:  missing ``sortKey()`` fixed in Zope

- #814378:  infinite reconnect recursion fixed

- #1560557: missing import

- #1242842: missing ``MULTI_STATEMENTS``

- #1226690: missing ``close()`` method


2.0.9
-----
- Allow the connection string to work without a specified database.

- Wrap queries with a lock to prevent multiple threads from using
  the connection simultaneously (this may or may not be happening).
  If transactional, then there is an additional transaction lock,
  acquired at the beginning of the transaction and released when
  either finished or aborted.

- A named lock can be specified by inserting ``*LOCKNAME`` at the start
  of the connection string. This is probably best used only if you
  must use non-transactional tables.

- Some stuff will be logged as an error when bad things happen
  during the transaction manager hooks.


2.0.8
-----
- More information about columns is available from the table
  browser. This is primarily to support SQL Blender.

- ``DECIMAL`` and ``NUMERIC`` columns now returned as floating-point numbers
  (was string). This has also been fixed in MySQLdb-0.9.1, but the
  fix is included here just in case you don't upgrade. Upgrading is
  a good idea anyway, because some memory-related bugs are fixed,
  particularly if using Zope 2.4 and Python 2.1.


2.0.7
-----
- Transaction support tweaked some more. A plus (``+``) or minus (``-``)
  at the beginning of the connection string will force transactions
  on or off respectively. By default, transactions are enabled if
  the server supports them. Beware: If you are using non-TST tables
  on a server that supports transactions, you should probably force
  transactions off.


2.0.6
-----
- This version finally should have all the transaction support
  working correctly. If your MySQL server supports transactions,
  i.e. it has at least one transaction-safe table (TST) handler,
  transactions are enabled automatically. If transactions are
  enabled, rollbacks (aborts) fail if any non-TST tables were
  modified.


2.0.5
-----
- Transactions don't really work right in this and prior versions.


2.0.4
-----
- ``INT`` columns, whether ``UNSIGNED`` or not, are returned as Python
  long integers to avoid overflows. Python-1.5.2 adds an ``L`` to
  the end of long integers when printing. Later versions do not.
  As a workaround, use affected columns with a format string,
  i.e. ``<dtml-var x fmt="%d">``.


2.0.0
-----
- This is the first version of the database adapter using MySQLdb
  for Zope.  This database adapter is based on the Z DCOracle DA
  version 2.2.0.
