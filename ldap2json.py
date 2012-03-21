#!/usr/bin/python

import os
import sys
import argparse
import ldap
import configobj
import pprint
import urllib
import json
import memcache

from bottle import route,run,request,HTTPError

directory = None
cache = None

class LDAPDirectory (object):

    def __init__ (self, uri, basedn='', scope=ldap.SCOPE_SUBTREE):
        self.basedn = basedn
        self.dir = ldap.initialize(uri)
        self.scope = scope

    def search(self, **kwargs):
        if basedn is None:
            basedn = self.basedn

        if not kwargs:
            kwargs = { 'objectclass': '*' }

        filter = self.build_filter(**kwargs)
        res = self.dir.search_s(basedn, self.scope, filterstr=filter) 
        return res

    def build_filter(self, **kwargs):
        filter = []
        for k,v in sorted(kwargs.items(), key=lambda x: x[0]):
            filter.append('(%s=%s)' % (k,v))

        if len(filter) > 1:
            return '(&%s)' % ''.join(filter)
        else:
            return filter[0]

@route('/ldap')
def ldapsearch():
    global directory
    global cache

    key = urllib.quote('/ldap/%s/%s' % (
            directory.basedn,
            request.urlparts.query,
            ))

    res = cache.get(key)

    if res is None:
        print 'need to fetch from directory'
        res = directory.search(**request.GET)
        cache.set(key, res, time=600)

    if not res:
        raise HTTPError(404)

    return json.dumps(res, indent=2)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-f', '--config',
            default='ldap2json.conf')
    return p.parse_args()

def main():
    global directory
    global cache

    opts = parse_args()

    config = configobj.ConfigObj(opts.config)

    pprint.pprint(config)

    cache = memcache.Client(
            config.get('memcache', {}).get('clients',
                '127.0.0.1:11211').split())

    directory = LDAPDirectory(
            config.get('ldap', {}).get(
                'uri', 'ldap://localhost'),
            config.get('ldap', {}).get(
                'basedn', ''))

    run()

if __name__ == '__main__':
    main()


