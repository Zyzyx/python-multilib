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
import multilib

# if you want to test the testing with the original mash code
# import mash.multilib as multilib

class test_methods(object):

    @classmethod
    def setup_class(cls):
        try:
            fd = bz2.BZ2File('testdata/RHEL-7.1-Server-x86_64.json.bz2', 'r')
            pj = json.load(fd)
        except IOError:
            print 'Run the tests in the same directory as multilib.py'
            print 'There should be a testdata subdirectory there'
            raise
        cls.packages = pj
        fd.close()

    @classmethod
    def teardown_class(cls):
        pass

    def print_fpo(self, fpo):
        fpod = fpo.convert()
        return '%s.%s' % (fpod['name'], fpod['arch'])

    def test_no(self):
        meth = multilib.NoMultilibMethod(None)
        for pinfo in self.packages.values():
            if not pinfo['details']:
                # None pops up when a 32-bit RPM was seen without a
                # corresponding 64-bit one of the same name. This can happen
                # because of dependencies I guess?
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            assert not meth.select(fpo), 'Should be False: %s' % self.print_fpo(fpo)

    def test_all(self):
        meth = multilib.AllMultilibMethod(None)
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            assert meth.select(fpo), 'Should be True: %s' % self.print_fpo(fpo)

    def test_kernel(self):
        meth = multilib.KernelMultilibMethod(None)
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            if fpo.arch.find('64') != -1:
                if fpo.name.startswith('kernel'):
                    provides = False
                    for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                        if p_name == 'kernel' or p_name == 'kernel-devel':
                            provides = True
                    if provides:
                        assert meth.select(fpo), 'Should be True: %s' % self.print_fpo(fpo)
                        continue
            assert not meth.select(fpo), 'Should be False: %s' % self.print_fpo(fpo)

    def test_yaboot(self):
        meth = multilib.YabootMultilibMethod(None)
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            if fpo.arch == 'ppc' and fpo.name.startswith('yaboot'):
                assert meth.select(fpo), 'Should be True: %s' % self.print_fpo(fpo)
            else:
                assert not meth.select(fpo), 'Should be False: %s' % self.print_fpo(fpo)

    def test_file(self):
        sect = 'runtime'
        meth = multilib.FileMultilibMethod(sect)
        cp = ConfigParser()
        cp.read('/etc/multilib.conf')
        self.list = cp.get(sect, 'white')
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            for item in meth.list:
                if fnmatch(fpo.name, item):
                    assert meth.select(fpo), 'Should be True: %s' % self.print_fpo(fpo)
                    continue
            assert not meth.select(fpo), 'Should be False: %s' % self.print_fpo(fpo)


    def test_runtime(self):
        meth = multilib.RuntimeMultilibMethod(None)
        sect = 'runtime'
        cp = ConfigParser()
        cp.read('/etc/multilib.conf')
        wl = cp.get(sect, 'white')
        bl = cp.get(sect, 'black')
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            if fpo.name in bl:
                assert not meth.select(fpo), 'Blacklisted, should be False: %s' % self.print_fpo(fpo)
                continue
            if fpo.name in wl:
                assert meth.select(fpo), 'Whitelisted, should be True: %s' % self.print_fpo(fpo)
                continue
            if not self.do_runtime(fpo, meth):
                assert not meth.select(fpo), 'should be False: %s' % self.print_fpo(fpo)

    def do_runtime(self, fpo, meth):
        if fpo.arch.find('64') != -1:
            if fpo.name in meth.PREFER_64:
                assert meth.select(fpo), 'preferred 64-bit, should be True: %s' % self.print_fpo(fpo)
                return True
            if fpo.name.startswith('kernel'):
                provides = False
                for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                    if p_name == 'kernel' or p_name == 'kernel-devel':
                        provides = True
                if provides:
                    assert meth.select(fpo), '64-bit kernel, should be True: %s' % self.print_fpo(fpo)
                    return True
        if fpo.name.startswith('kernel'):
            # looks redundant, but we're not 64-bit here
            for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                if p_name == 'kernel':
                    assert not meth.select(fpo), '32-bit kernel should be False: %s' % self.print_fpo(fpo)
                    return False
        for file in fpo.returnFileEntries():
            (dirname, filename) = file.rsplit('/', 1)
            # libraries in standard dirs
            if dirname in meth.LIBDIRS and fnmatch(filename, '*.so.*'):
                assert meth.select(fpo), '.so.x files, should be True: %s' % self.print_fpo(fpo)
                return True
            if dirname in meth.by_dir:
                assert meth.select(fpo), 'std dirs, should be True: %s' % self.print_fpo(fpo)
                return True
            # mysql, qt, etc.
            if dirname == '/etc/ld.so.conf.d' and filename.endswith('.conf'):
                assert meth.select(fpo), 'ld config, should be True: %s' % self.print_fpo(fpo)
                return True
            # nss (Some nss modules end in .so instead of .so.X)
            # db (db modules end in .so instead of .so.X)
            if dirname in meth.ROOTLIBDIRS and (filename.startswith('libnss_') or filename.startswith('libdb-')):
                assert meth.select(fpo), '.so files, should be True: %s' % self.print_fpo(fpo)
                return True
            # Optimization:
            # All tests beyond here are for things in USRLIBDIRS
            if not dirname.startswith(tuple(meth.USRLIBDIRS)):
                # The dirname does not start with a USRLIBDIR so we can move
                # on to the next file
                continue
            if dirname.startswith(('/usr/lib/gtk-2.0', '/usr/lib64/gtk-2.0')):
                # gtk2-engines
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/engines'):
                    assert meth.select(fpo), 'gtk2 engines should be True: %s' % self.print_fpo(fpo)
                    return True
                # accessibility
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/modules'):
                    assert meth.select(fpo), 'accessibility should be True: %s' % self.print_fpo(fpo)
                    return True
                # scim-bridge-gtk
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/immodules'):
                    assert meth.select(fpo), 'scim-bridge-gtk should be True: %s' % self.print_fpo(fpo)
                    return True
                # images
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/loaders'):
                    assert meth.select(fpo), 'image loaders should be True: %s' % self.print_fpo(fpo)
                    return True
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/printbackends'):
                    assert meth.select(fpo), 'image backends should be True: %s' % self.print_fpo(fpo)
                    return True
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/filesystems'):
                    assert meth.select(fpo), 'gtk filesystems should be True: %s' % self.print_fpo(fpo)
                    return True
                # Optimization:
                # No tests beyond here for things in /usr/lib*/gtk-2.0
                continue
            # gstreamer
            if dirname.startswith(('/usr/lib/gstreamer-', '/usr/lib64/gstreamer-')):
                assert meth.select(fpo), 'gstreamer should be True: %s' % self.print_fpo(fpo)
                return True
            # qt/kde fun
            if fnmatch(dirname, '/usr/lib*/qt*/plugins/*'):
                assert meth.select(fpo), 'qt plugins should be True: %s' % self.print_fpo(fpo)
                return True
            if fnmatch(dirname, '/usr/lib*/kde*/plugins/*'):
                assert meth.select(fpo), 'kde plugins should be True: %s' % self.print_fpo(fpo)
                return True
            # qml
            if fnmatch(dirname, '/usr/lib*/qt5/qml/*'):
                assert meth.select(fpo), 'qml should be True: %s' % self.print_fpo(fpo)
                return True
            # images
            if fnmatch(dirname, '/usr/lib*/gdk-pixbuf-2.0/*/loaders'):
                assert meth.select(fpo), 'gdk-pixbuf should be True: %s' % self.print_fpo(fpo)
                return True
            # xine-lib
            if fnmatch(dirname, '/usr/lib*/xine/plugins/*'):
                assert meth.select(fpo), 'xine-lib should be True: %s' % self.print_fpo(fpo)
                return True
            # oprofile
            if dirname in meth.OPROFILEDIRS and fnmatch(filename, '*.so.*'):
                assert meth.select(fpo), 'oprofile should be True: %s' % self.print_fpo(fpo)
                return True
            # wine
            if dirname in meth.WINEDIRS and filename.endswith('.so'):
                assert meth.select(fpo), 'wine .so should be True: %s' % self.print_fpo(fpo)
                return True
            # sane drivers
            if dirname in meth.SANEDIRS and filename.startswith('libsane-'):
                assert meth.select(fpo), 'sane drivers should be True: %s' % self.print_fpo(fpo)
                return True
        return False

    def test_devel(self):
        sect = 'devel'
        cp = ConfigParser()
        cp.read('/etc/multilib.conf')
        wl = cp.get(sect, 'white')
        bl = cp.get(sect, 'black')
        meth = multilib.DevelMultilibMethod(None)
        for pinfo in self.packages.values():
            if not pinfo['details']:
                continue
            fpo = fakepo.FakePackageObject(d=pinfo['details'])
            if fpo.name in bl:
                assert not meth.select(fpo), 'Blacklisted, should be False: %s' % self.print_fpo(fpo)
                continue
            if fpo.name in wl:
                assert meth.select(fpo), 'Whitelisted, should be True: %s' % self.print_fpo(fpo)
                continue
            if self.do_runtime(fpo, meth):
                # returns True if a value was identified and asserted, False otherwise
                continue
            if fpo.name.startswith('ghc-'):
                assert not meth.select(fpo), 'ghc package, should be False: %s' % self.print_fpo(fpo)
                continue
            if fpo.name.startswith('kernel'):
                # looks redundant, but we're not 64-bit here
                for (p_name, p_flag, (p_e, p_v, p_r)) in fpo.provides:
                    if p_name == 'kernel-devel':
                        assert not meth.select(fpo), 'kernel-devel, should be False: %s' % self.print_fpo(fpo)
                        continue
                    if p_name.endswith('-devel') or p_name.endswith('-static'):
                        assert meth.select(fpo), 'kernel-*-devel, should be True: %s' % self.print_fpo(fpo)
                        continue
            if fpo.name.endswith('-devel'):
                assert meth.select(fpo), '-devel package, should be True: %s' % self.print_fpo(fpo)
                continue
            if fpo.name.endswith('-static'):
                assert meth.select(fpo), '-static package, should be True: %s' % self.print_fpo(fpo)
                continue
            assert not meth.select(fpo), 'should be False: %s' % self.print_fpo(fpo)
