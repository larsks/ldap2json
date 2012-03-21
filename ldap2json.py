#!/usr/bin/python

'''ldap2json acts as a proxy between HTTP GET requests and an LDAP
directory.  Results are returned to the caller using JSON.'''

import os
import sys
import argparse
import ldap
import configobj
import pprint
import urllib
import json
import memcache

from bottle import route,run,request,response,HTTPError

directory = None
cache = None
config = None

class LDAPDirectory (object):
    '''A simple wrapper for LDAP connections that exposes a simplified
    search interface.  At the moment this class only supports anonymous
    binds.'''

    def __init__ (self, uri,
            basedn='',
            scope=ldap.SCOPE_SUBTREE,
            debug=False
            ):

        self.uri    = uri
        self.basedn = basedn
        self.scope  = scope
        self.debug  = debug

        self.init_ldap()

    def init_ldap(self):
        self.dir    = ldap.initialize(self.uri)

    def search(self, **kwargs):
        '''Turns kwargs into an LDAP search filter, executes the search,
        and returns the results.  The keys in kwargs are ANDed together;
        only results meeting *all* criteria will be returned.'''

        if not kwargs:
            kwargs = { 'objectclass': '*' }

        filter = self.build_filter(**kwargs)
        res = self.dir.search_s(self.basedn, self.scope, filterstr=filter) 
        return res

    def build_filter(self, **kwargs):
        '''Transform a dictionary into an LDAP search filter.'''

        filter = []
        for k,v in sorted(kwargs.items(), key=lambda x: x[0]):
            filter.append('(%s=%s)' % (k,v))

        if len(filter) > 1:
            return '(&%s)' % ''.join(filter)
        else:
            return filter[0]

class Cache (object):
    '''This is a very simple wrapper over memcache.Client that
    lets us specify a default lifetime for cache objects.'''

    def __init__ (self, servers, lifetime=600):
        self.lifetime = lifetime
        self.cache = memcache.Client(servers)

    def set(self, k, v):
        self.cache.set(k, v, time=self.lifetime)

    def get(self, k):
        return self.cache.get(k)

@route('/ldap')
def ldapsearch():
    '''This method is wqhere web clients interact with ldap2json.  Any
    request parameters are turned into an LDAP filter, and results are JSON
    encoded and returned to the caller.'''

    global directory
    global cache
    global config

    key = urllib.quote('/ldap/%s/%s' % (
            directory.basedn,
            request.urlparts.query,
            ))

    res = cache.get(key)

    if res is None:
        res = directory.search(**request.GET)
        cache.set(key, res)

    if not res:
        raise HTTPError(404)

    if config.get('debug'):
        print 'result:', res

    response.content_type = 'application/json'
    return json.dumps(res, indent=2)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--debug', action='store_true',
            default=None)
    p.add_argument('-f', '--config',
            default='ldap2json.conf')
    return p.parse_args()

def init_memcache():
    global config
    global cache

    # Extract server list from config file.
    servers = config.get('memcache', {}).get(
            'servers', '127.0.0.1:11211')
    lifetime = config.get('memcache', {}).get('lifetime', 600)

    # Make sure we have a Python list of servers.
    if isinstance(servers, (str, unicode)):
        servers = [servers]

    # Make sure we have an integer.
    lifetime = int(lifetime)

    assert lifetime > 0
    assert isinstance(servers, list)

    if config.get('debug'):
        print >>sys.stderr, 'using memcache servers: %s' % (
                servers)

    cache = Cache(servers, lifetime=lifetime)

def init_directory():
    global directory
    global config

    uri    = config.get('ldap', {}).get( 'uri', 'ldap://localhost')
    basedn = config.get('ldap', {}).get( 'basedn', '')
    
    directory = LDAPDirectory(
            uri,
            basedn=basedn,
            debug=config.get('debug'),
            )

def main():
    global directory
    global cache
    global config

    opts = parse_args()

    config = configobj.ConfigObj(opts.config)

    # Only override config file "debug" setting if --debug
    # was explicitly passed on the command line.
    if opts.debug is not None:
        config['debug'] = opts.debug

    if config.get('debug'):
        print >>sys.stderr, 'CONFIG:', pprint.pformat(dict(config))

    init_memcache()
    init_directory()

    run(
            host=config.get('host', '127.0.0.1'),
            port=config.get('port', 8080),
            reloader=config.get('debug', False),
            )

if __name__ == '__main__':
    main()


