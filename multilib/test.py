#!/usr/bin/python -tt

try:
    # RHEL 6 and earlier
    import simplejson as json
except ImportError:
    # RHEL 7 and later
    import json

import bz2
from ConfigParser import ConfigParser
import fakepo
from fnmatch import fnmatch
from multilib import multilib
import os

# if you want to test the testing with the original mash code
#import mash.multilib as multilib

class test_methods(object):

    @classmethod
    def setup_class(cls):
        # read test data
        try:
            files = os.listdir('testdata')
        except OSError:
            print 'There should be a testdata subdirectory in your CWD, and'
            print 'note only the first .json.bz2 file found will be considered'
            raise
        pj = None
        for f in files:
            if fnmatch(f, '*.json.bz2'):
                fd = bz2.BZ2File('testdata/RHEL-7.1-Server-x86_64.json.bz2', 'r')
                pj = json.load(fd)
                break # just take the first hit
        assert pj, 'No test data found in testdata, create some with the multilib_test_data script'
        cls.packages = pj
        fd.close()

        # read multilib configuration
        cls.conffile = '/etc/multilib.conf'
        cp = ConfigParser()
        assert len(cp.read(cls.conffile)) == 1, 'missing ' + cls.conffile
        cls.conf = cp
        cls.archmap = {'ppc64': 'ppc', 'x86_64': 'i686'}
        cls.revarchmap = dict((v, k) for k, v in cls.archmap.items())

    def disable_test(self):
        def wrapper(func):
             func.__test__ = False
             return func
        return wrapper

    def print_fpo(self, fpo):
        fpod = fpo.convert()
        return '%s.%s' % (fpod['name'], fpod['arch'])

    def confirm_true(self, fpo, meth, msg='should be true'):
        """confirm that a package is multilib in code and in test data"""
        code = meth.select(fpo)
        key = '%s.%s' % (fpo.name, fpo.arch)
        msg += ' (%s)' % self.print_fpo(fpo)
        print key
        print '  code says %s' % code
        if meth.name == 'devel':
            # the data assumes the 'devel' method was used in compose
            if fpo.arch in self.archmap.keys():
                # this is 64-bit
                key32 = '%s.%s' % (fpo.name, self.archmap[fpo.arch])
                data = self.packages.has_key(key32)
            else:
                # this is a 32-bit package
                key64 = '%s.%s' % (fpo.name, self.revarchmap[fpo.arch])
                data = self.packages.has_key(key64)
            print '  data says %s' % data
            assert code and data, msg
        assert code, msg
        return True

    def confirm_false(self, fpo, meth, msg='should be false'):
        """confirm that a package is NOT multilib in code and in test data"""
        code = meth.select(fpo)
        key = '%s.%s' % (fpo.name, fpo.arch)
        msg += ' (%s)' % self.print_fpo(fpo)
        print key
        print '  code says %s' % code
        if meth.name == 'devel':
            # the data assumes the 'devel' method was used in compose
            if fpo.arch in self.archmap.keys():
                # this is 64-bit
                key32 = '%s.%s' % (fpo.name, self.archmap[fpo.arch])
                data = self.packages.has_key(key32)
            else:
                # this is a 32-bit package
                key64 = '%s.%s' % (fpo.name, self.revarchmap[fpo.arch])
                data = self.packages.has_key(key64)
            print '  data says %s' % data
            assert not code and not data, msg
        assert not code, msg
        return True

    def do_runtime(self, fpo, meth):
        """
        This method returns True if we tested a result, or None if we are
        still unsure of what the result should be.
        """
        sect = 'runtime'
        wl = self.conf.get(sect, 'white')
        bl = self.conf.get(sect, 'black')
        if fpo.name in bl:
            return self.confirm_false(fpo, meth, 'Blacklisted, should be False')
        if fpo.name in wl:
            return self.confirm_true(fpo, meth, 'Whitelisted, should be True')
        if fpo.arch.find('64') != -1:
            if fpo.name in meth.PREFER_64:
                return self.confirm_true(fpo, meth, 'preferred 64-bit, should be True')
            if fpo.name.startswith('kernel'):
                provides = False
                for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                    if p_name == 'kernel' or p_name == 'kernel-devel':
                        provides = True
                if provides:
                    return self.confirm_true(fpo, meth, '64-bit kernel, should be True')
        if fpo.name.startswith('kernel'):
            # looks redundant, but we're not 64-bit here
            for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                if p_name == 'kernel':
                    return self.confirm_false(fpo, meth, '32-bit kernel should be False')
        for file in fpo.returnFileEntries():
            (dirname, filename) = file.rsplit('/', 1)
            # libraries in standard dirs
            if dirname in meth.LIBDIRS and fnmatch(filename, '*.so.*'):
                return self.confirm_true(fpo, meth, '.so.x files, should be True')
            if dirname in meth.by_dir:
                return self.confirm_true(fpo, meth, 'std dirs, should be True')
            # mysql, qt, etc.
            if dirname == '/etc/ld.so.conf.d' and filename.endswith('.conf'):
                return self.confirm_true(fpo, meth, 'ld config, should be True')
            # nss (Some nss modules end in .so instead of .so.X)
            # db (db modules end in .so instead of .so.X)
            if dirname in meth.ROOTLIBDIRS and (filename.startswith('libnss_') or filename.startswith('libdb-')):
                return self.confirm_true(fpo, meth, '.so files, should be True: %s')
            # Optimization:
            # All tests beyond here are for things in USRLIBDIRS
            if not dirname.startswith(tuple(meth.USRLIBDIRS)):
                # The dirname does not start with a USRLIBDIR so we can move
                # on to the next file
                continue
            if dirname.startswith(('/usr/lib/gtk-2.0', '/usr/lib64/gtk-2.0')):
                # gtk2-engines
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/engines'):
                    return self.confirm_true(fpo, meth, 'gtk2 engines should be True')
                # accessibility
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/modules'):
                    return self.confirm_true(fpo, meth, 'gtk accessibility should be True')
                # scim-bridge-gtk
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/immodules'):
                    return self.confirm_true(fpo, meth, 'scim-bridge-gtk should be True')
                # images
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/loaders'):
                    return self.confirm_true(fpo, meth, 'image loaders should be True')
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/printbackends'):
                    return self.confirm_true(fpo, meth, 'image backends should be True')
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/filesystems'):
                    return self.confirm_true(fpo, meth, 'gtk filesystems should be True')
                # Optimization:
                # No tests beyond here for things in /usr/lib*/gtk-2.0
                continue
            # gstreamer
            if dirname.startswith(('/usr/lib/gstreamer-', '/usr/lib64/gstreamer-')):
                return self.confirm_true(fpo, meth, 'gstreamer should be True')
            # qt/kde fun
            if fnmatch(dirname, '/usr/lib*/qt*/plugins/*'):
                return self.confirm_true(fpo, meth, 'qt plugins should be True')
            if fnmatch(dirname, '/usr/lib*/kde*/plugins/*'):
                return self.confirm_true(fpo, meth, 'kde plugins should be True')
            # qml
            if fnmatch(dirname, '/usr/lib*/qt5/qml/*'):
                return seflf.confirm_true(fpo, meth, 'qml should be True')
            # images
            if fnmatch(dirname, '/usr/lib*/gdk-pixbuf-2.0/*/loaders'):
                return self.confirm_true(fpo, meth, 'gdk-pixbuf should be True')
            # xine-lib
            if fnmatch(dirname, '/usr/lib*/xine/plugins/*'):
                return self.confirm_true(fpo, meth, 'xine-lib should be True')
            # oprofile
            if dirname in meth.OPROFILEDIRS and fnmatch(filename, '*.so.*'):
                return self.confirm_true(fpo, meth, 'oprofile should be True')
            # wine
            if dirname in meth.WINEDIRS and filename.endswith('.so'):
                return self.confirm_true(fpo, meth, 'wine .so should be True')
            # sane drivers
            if dirname in meth.SANEDIRS and filename.startswith('libsane-'):
                return self.confirm_true(fpo, meth, 'sane drivers should be True')

    # test methods executed by nose start here

    def test_no(self):
        meth = multilib.NoMultilibMethod(None)
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            self.confirm_false(fpo, meth)

    def test_all(self):
        meth = multilib.AllMultilibMethod(None)
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            self.confirm_true(fpo, meth)

    def test_kernel(self):
        meth = multilib.KernelMultilibMethod(None)
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            if fpo.arch.find('64') != -1:
                if fpo.name.startswith('kernel'):
                    provides = False
                    for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                        if p_name == 'kernel' or p_name == 'kernel-devel':
                            provides = True
                    if provides:
                        self.confirm_true(fpo, meth)
                        continue
            self.confirm_false(fpo, meth)

    def test_yaboot(self):
        meth = multilib.YabootMultilibMethod(None)
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            if fpo.arch == 'ppc' and fpo.name.startswith('yaboot'):
                self.confirm_true(fpo, meth)
            else:
                self.confirm_false(fpo, meth)

    # if using mash.multilib, uncomment this. Test is known to fail since the
    # input file format changed in python-multilib
    # @disable_test
    def test_file(self):
        sect = 'multilib'
        self.list = self.conf.get(sect, 'packages')
        meth = multilib.FileMultilibMethod(self.conffile)
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            for item in meth.list:
                if fnmatch(fpo.name, item):
                    self.confirm_true(fpo, meth)
                    break
            self.confirm_false(fpo, meth)

    def test_runtime(self):
        meth = multilib.RuntimeMultilibMethod()
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            if not self.do_runtime(fpo, meth):
                self.confirm_false(fpo, meth)

    def test_devel(self):
        sect = 'devel'
        wl = self.conf.get(sect, 'white')
        bl = self.conf.get(sect, 'black')
        meth = multilib.DevelMultilibMethod()
        for pinfo in self.packages.values():
            fpo = fakepo.FakePackageObject(d=pinfo)
            if fpo.name in bl:
                self.confirm_false(fpo, meth, 'Blacklisted, should be False')
            elif fpo.name in wl:
                self.confirm_true(fpo, meth, 'Whitelisted, should be True')
            elif self.do_runtime(fpo, meth):
                # returns True if a value was identified and asserted
                # False otherwise
                pass
            elif fpo.name.startswith('ghc-'):
                self.confirm_false(fpo, meth, 'ghc package, should be False')
            elif fpo.name.startswith('kernel'):
                # looks redundant, but we're not 64-bit here
                is_kd, is_dev = False, False
                for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                    if p_name == 'kernel-devel':
                        is_kd = True
                        break
                    if p_name.endswith('-devel') or p_name.endswith('-static'):
                        is_dev = True
                        break
                if is_kd:
                    self.confirm_false(fpo, meth, 'kernel-devel, should be False')
                elif is_dev:
                    self.confirm_true(fpo, meth, 'kernel-*-devel, should be True')
            elif fpo.name.endswith('-devel'):
                self.confirm_true(fpo, meth, '-devel package, should be True')
            elif fpo.name.endswith('-static'):
                self.confirm_true(fpo, meth, '-static package, should be True')
            else:
                self.confirm_false(fpo, meth)
