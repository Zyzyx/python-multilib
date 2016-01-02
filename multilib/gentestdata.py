#!/usr/bin/python -tt

from glob import glob
import logging
from optparse import OptionParser
import os
import yum.packages

try:
    # RHEL 6 and earlier
    import simplejson as json
except ImportError:
    # RHEL 7 and later
    import json

import fakepo

# generate test data for multilib
# accepts a path to a compose and writes out a bigass json file with multlib
# stuff

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def get_options():
    parser = OptionParser(usage='%prog [options] path-to-compose')
    parser.add_option('-d', '--debug', default=False, action='store_true')
    parser.add_option('-o', '--outfile', default='multilib_data.json')
    opts, args = parser.parse_args()
    if len(args) != 1:
        parser.error('you must provide a path to a compose')
    if opts.debug:
        log.setLevel(logging.DEBUG)
    return opts, args[0]

def get_fpo(rpmfile):
    """return a fake yum PackageObject for a given RPM"""
    po = yum.packages.YumLocalPackage(filename=rpmfile)
    return fakepo.FakePackageObject(po=po)

def find_repos(cpath):
    """generator to recursively go down a path and find yum repositories"""
    for (dirpath, dirnames, _) in os.walk(cpath):
        if 'repodata' in dirnames:
            # make sure this is a repo for a multilib-supporting arch
            for arch in ('ppc64', 'x86_64'):
                if arch in dirpath:
                    ppath = dirpath
                    rpms = glob(os.path.join(dirpath, '*.rpm'))
                    if len(rpms) == 0:
                        log.debug('no rpms in base dir')
                        ppath = os.path.join(dirpath, 'Packages')
                        rpms = glob(os.path.join(ppath, '*.rpm'))
                        if len(rpms) == 0:
                            log.debug('no rpms in Packages')
                            continue
                    yield ppath
        for deeperdir in dirnames:
            find_repos(os.path.join(dirpath, deeperdir))

if __name__ == '__main__':
    opts, compose_path = get_options()
    data = {}
    for repo in find_repos(compose_path):
        log.info('processing %s' % repo)
        for rpmf in glob(os.path.join(repo, '*.rpm')):
            fpo = get_fpo(rpmf)
            if 'debuginfo' in fpo.name:
                # debuginfos never have multilib, skip for brevity's sake
                continue
            key = '%s.%s' % (fpo.name, fpo.arch)
            data[key] = fpo.convert()
    fd = open(opts.outfile, 'w')
    json.dump(data, fd, indent=2, sort_keys=True)
    fd.close()
    log.info('data written to %s' % opts.outfile)
