# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
from fnmatch import fnmatch
from ConfigParser import ConfigParser

class MultilibMethod(object):
    PREFER_64 = frozenset(
        ('gdb', 'frysk', 'systemtap', 'systemtap-runtime', 'ltrace', 'strace'))

    def __init__(self, config):
        self.name = 'base'

    def select(self, po):
        if po.arch.find('64') != -1:
            if po.name in self.PREFER_64:
                return True
            if po.name.startswith('kernel'):
                for (p_name, p_flag, (p_e, p_v, p_r)) in po.provides:
                    if p_name == 'kernel' or p_name == 'kernel-devel':
                        return True
        return False


class NoMultilibMethod(object):

    def __init__(self, config):
        self.name = 'none'

    def select(self, po):
        return False


class AllMultilibMethod(MultilibMethod):

    def __init__(self, config):
        self.name = 'all'

    def select(self, po):
        return True


class FileMultilibMethod(MultilibMethod):

    def __init__(self, config='/etc/multilib.conf'):
        self.name = 'file'
        self.cp = ConfigParser()
        self.cp.read(config)
        self.list = self.cp.get('multilib', 'packages')

    def select(self, po):
        for item in self.list:
            if fnmatch(po.name, item):
                return True
        return False


class KernelMultilibMethod(object):

    def __init__(self, config):
        self.name = 'base'

    def select(self, po):
        if po.arch.find('64') != -1:
            if po.name.startswith('kernel'):
                for (p_name, p_flag, (p_e, p_v, p_r)) in po.provides:
                    if p_name == 'kernel' or p_name == 'kernel-devel':
                        return True
        return False


class YabootMultilibMethod(object):

    def __init__(self, config):
        self.name = 'base'

    def select(self, po):
        if po.arch in ['ppc']:
            if po.name.startswith('yaboot'):
                return True
        return False


class RuntimeMultilibMethod(MultilibMethod):
    ROOTLIBDIRS = frozenset(('/lib', '/lib64'))
    USRLIBDIRS = frozenset(('/usr/lib', '/usr/lib64'))
    LIBDIRS = ROOTLIBDIRS.union(USRLIBDIRS)
    OPROFILEDIRS = frozenset(('/usr/lib/oprofile', '/usr/lib64/oprofile'))
    WINEDIRS = frozenset(('/usr/lib/wine', '/usr/lib64/wine'))
    SANEDIRS = frozenset(('/usr/lib/sane', '/usr/lib64/sane'))

    by_dir = set()

    # alsa, dri, gtk-accessibility, scim-bridge-gtk, krb5, sasl, vdpau
    by_dir.update(frozenset(os.path.join('/usr/lib', p) for p in ('alsa-lib',
                                                                  'dri', 'gtk-2.0/modules', 'gtk-2.0/immodules', 'krb5/plugins',
                                                                  'sasl2', 'vdpau')))
    by_dir.update(frozenset(os.path.join('/usr/lib64', p) for p in ('alsa-lib',
                                                                    'dri', 'gtk-2.0/modules', 'gtk-2.0/immodules', 'krb5/plugins',
                                                                    'sasl2', 'vdpau')))

    # pam
    by_dir.update(frozenset(os.path.join(p, 'security') for p in ROOTLIBDIRS))

    # lsb
    by_dir.add('/etc/lsb-release.d')

    def __init__(self, config='/etc/multilib.conf'):
        self.name = 'runtime'
        self.cp = ConfigParser()
        self.cp.readfp(open(config, 'r'))
        self.runtime_whitelist = self.cp.get(self.name, 'white')
        self.runtime_blacklist = self.cp.get(self.name, 'black')

    def select(self, po):
        if po.name in self.runtime_blacklist:
            return False
        if po.name in self.runtime_whitelist:
            return True
        if MultilibMethod.select(self, po):
            return True
        if po.name.startswith('kernel'):
            for (p_name, p_flag, (p_e, p_v, p_r)) in po.provides:
                if p_name == 'kernel':
                    return False
        for file in po.returnFileEntries():
            (dirname, filename) = file.rsplit('/', 1)

            # libraries in standard dirs
            if dirname in self.LIBDIRS and fnmatch(filename, '*.so.*'):
                return True
            if dirname in self.by_dir:
                return True
            # mysql, qt, etc.
            if dirname == '/etc/ld.so.conf.d' and filename.endswith('.conf'):
                return True
            # nss (Some nss modules end in .so instead of .so.X)
            # db (db modules end in .so instead of .so.X)
            if dirname in self.ROOTLIBDIRS and (filename.startswith('libnss_') or filename.startswith('libdb-')):
                return True
            # Optimization:
            # All tests beyond here are for things in USRLIBDIRS
            if not dirname.startswith(tuple(self.USRLIBDIRS)):
                # The dirname does not start with a USRLIBDIR so we can move
                # on to the next file
                continue

            if dirname.startswith(('/usr/lib/gtk-2.0', '/usr/lib64/gtk-2.0')):
                # gtk2-engines
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/engines'):
                    return True
                # accessibility
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/modules'):
                    return True
                # scim-bridge-gtk
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/immodules'):
                    return True
                # images
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/loaders'):
                    return True
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/printbackends'):
                    return True
                if fnmatch(dirname, '/usr/lib*/gtk-2.0/*/filesystems'):
                    return True
                # Optimization:
                # No tests beyond here for things in /usr/lib*/gtk-2.0
                continue

            # gstreamer
            if dirname.startswith(('/usr/lib/gstreamer-', '/usr/lib64/gstreamer-')):
                return True
            # qt/kde fun
            if fnmatch(dirname, '/usr/lib*/qt*/plugins/*'):
                return True
            if fnmatch(dirname, '/usr/lib*/kde*/plugins/*'):
                return True
            # qml
            if fnmatch(dirname, '/usr/lib*/qt5/qml/*'):
                return True
            # images
            if fnmatch(dirname, '/usr/lib*/gdk-pixbuf-2.0/*/loaders'):
                return True
            # xine-lib
            if fnmatch(dirname, '/usr/lib*/xine/plugins/*'):
                return True
            # oprofile
            if dirname in self.OPROFILEDIRS and fnmatch(filename, '*.so.*'):
                return True
            # wine
            if dirname in self.WINEDIRS and filename.endswith('.so'):
                return True
            # sane drivers
            if dirname in self.SANEDIRS and filename.startswith('libsane-'):
                return True
        return False


class DevelMultilibMethod(RuntimeMultilibMethod):

    def __init__(self, config='/etc/multilib.conf'):
        super(DevelMultilibMethod, self).__init__(config)
        self.name = 'devel'
        self.devel_whitelist = self.cp.get(self.name, 'white')
        self.devel_blacklist = self.cp.get(self.name, 'black')

    def select(self, po):
        if po.name in self.devel_blacklist:
            return False
        if po.name in self.devel_whitelist:
            return True
        if RuntimeMultilibMethod.select(self, po):
            return True
        if po.name.startswith('ghc-'):
            return False
        if po.name.startswith('kernel'):
            for (p_name, p_flag, (p_e, p_v, p_r)) in po.provides:
                if p_name == 'kernel-devel':
                    return False
                if p_name.endswith('-devel') or p_name.endswith('-static'):
                    return True
        if po.name.endswith('-devel'):
            return True
        if po.name.endswith('-static'):
            return True
        return False
