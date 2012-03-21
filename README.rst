ldap2json
=========

A simple proxy that turns HTTP GET requests into LDAP queries and
then returns JSON-encoded results.

Requirements
============

ldap2json requires the bottle_ framework, the ldap_ module, the configobj_
module, the memcache_ module, and a recent version of Python (where
"recent" means "has `argparse`").

.. _bottle: http://bottlepy.org/
.. _ldap: http://www.python-ldap.org/
.. _configobj: http://www.voidspace.org.uk/python/configobj.html
.. _memcache: http://www.tummy.com/Community/software/python-memcached/

Running ldap2json
=================

Running ldap2json from the command line::

  ./ldap2json.py [ -f configfile ]

Return values
=============

If a search returns an empty result, ldap2json will return a 404 status
code to the caller.

Otherwise, the return value is a list of *[DN, attribute_dictionary]*
tuples, where *DN* is the distinguished name of the record and
*attribute_dictionary* is a key/value dictionary of attributes.  The values
of the attribute dictionary will *always* be lists, even if attributes are
single-valued.

Configuration
==============

ldap2json uses a simple INI-style configuration file.  

Global settings
---------------

The global section of the config file may contain values for the following:

- ``host`` -- Bind address for the web application.
- ``port`` -- Port on which to listen.
- ``debug`` -- Enable some debugging output if true.  This will also cause
  ``bottle`` to reload the server if the source files change.

ldap
----

The ``ldap`` section may contain two values:

- ``uri`` -- an ``ldap://`` URI specifying the endpoint for queries.
- ``basedn`` -- the base DN to use for searches.

An example `ldap` section might look like this::

  [ldap]
  
  uri = ldap://ldap.example.com
  basedn = "ou=people, dc=example, dc=com"

Note that due to my use of the `configobj` module, strings containing
commas must be quoted.

memcache
--------

ldap2json will use memcache, if it's available, for caching results.  The
``memcache`` section may contain values for the following:

- ``servers`` -- a comma-separated list of memcache ``host:port`` servers.
- ``lifetime`` -- the lifetime of items added to the cache.

An example ``memcache`` section might look like this::

  [memcache]

  servers = 127.0.0.1:11211
  lifetime = 600

An example
==========

Assuming that the server is running on ``localhost`` port ``8080``, the
following::

  $ curl http://localhost:8080/ldap?cn=alice*

Might return something like this::

  [
    [
      "uid=alice,ou=people,o=Example Organization,c=US", 
      {
        "telephoneNumber": [
          "+1-617-555-1212"
        ], 
        "description": [
          "employee"
        ], 
        "title": [
          "Ninja"
        ], 
        "sn": [
          "Person"
        ], 
        "mail": [
          "alice@example.com"
        ], 
        "givenName": [
          "Alice"
        ], 
        "cn": [
          "Alice Person"
        ]
      }
    ]
  ]

