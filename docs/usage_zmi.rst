Usage from the Zope ZMI
=======================
The database connection object can be manipulated in the :term:`Zope`
:term:`ZMI` on a series of screens, accessible through named tabs in
the main window.

Status
------
Shows the database connection status and allows the user to open or
close the connection.

Properties
----------
Edit the database connection attributes and apply any changes.

Test
----
The Test tab can be used as long as the database connection is connected.
You can enter SQL statements into the text field and view the results
sent back from the database.

Security
--------
Change the :term:`Zope` role to permission mappings here.

Undo
----
If your particular :term:`ZODB` flavor supports it, you can undo
:term:`Zope` transactions affecting the database connector object here.
These transactions don't reflect relational database transactions in the
underlying MySQL or MariaDB databases, only :term:`ZODB` transactions.

Ownership
---------
Information about the :term:`Zope` user who owns the database connector
object. Ownership in the :term:`Zope` sense confers additional rights.

Interfaces
----------
View and change the :term:`Zope` :term:`Interface` assignments for the
database connector object.

Browse
------
You can browse the database tables and columns from the relational database
specified in the connection string.
