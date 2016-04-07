Name:       python-multilib
Version:    1.1
Release:    2%{?dist}
Summary:    A module for determining if a package is multilib or not
Group:      Development/Libraries
License:    GPLv2
URL:        https://github.com/Zyzyx/python-multilib/
Source0:    %{name}-%{version}.tar.bz2

BuildArch:      noarch
%description
A Python module that supports several multilib "methods" useful for determining
if a 32-bit package should be included with its 64-bit analogue in a compose.

%package -n python2-multilib
Summary:        A module for determining if a package is multilib or not
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
Requires:       python2

%description -n python2-multilib
A Python module that supports several multilib "methods" useful for determining
if a 32-bit package should be included with its 64-bit analogue in a compose.

%package -n python3-multilib
Summary:        A module for determining if a package is multilib or not
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       python3

%description -n python3-multilib
A Python module that supports several multilib "methods" useful for determining
if a 32-bit package should be included with its 64-bit analogue in a compose.



%prep
%setup -q


%build
%py2_build
#py3_build

%install
%py2_install
#py3_install

%check
#{__python2} setup.py test
#{__python3} setup.py test

%files -n python2-multilib
%license LICENSE
%doc README.md
%{python2_sitelib}/*
%config(noreplace) %{_sysconfdir}/multilib.conf

#files -n python3-multilib
#license LICENSE
#doc README.md
#{python3_sitelib}/*

%changelog
* Thu Apr 07 2016 Dennis Gilmore <dennis@ausil.us> - 1.1-2
- setup to make python3 down the road.
- spec and srpm named python-multilib
- fix license

* Tue Jul 21 2009 Jay Greguske <jgregusk@redhat.com> - 1.1-1
- consider dependencies in multilib testing
- fix a couple import errors

* Tue Jul 21 2009 Jay Greguske <jgregusk@redhat.com> - 1.0-1
- Initial RPM release
