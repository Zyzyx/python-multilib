Name:       python2-multilib
Version:    1.1
Release:    1%{?dist}
Summary:    a module for determining if a package is multilib or not
Group:      Development/Libraries
License:    GPLv3+
URL:        https://github.com/Zyzyx/python-multilib/archive/master.zip
Source0:    %{name}-%{version}.tar.gz

BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python
BuildArch:      noarch

%description
A Python module that supports several multilib "methods" useful for determining
if a 32-bit package should be included with its 64-bit analogue in a compose.

%prep
%setup -q


%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --root %{buildroot}


%files
%{python_sitelib}/*
%{_bindir}/multilib_test_data
%doc README.md LICENSE
%{_sysconfdir}/multilib.conf


%changelog
* Tue Jul 21 2009 Jay Greguske <jgregusk@redhat.com> - 1.1-1
- consider dependencies in multilib testing
- fix a couple import errors
* Tue Jul 21 2009 Jay Greguske <jgregusk@redhat.com> - 1.0-1
- Initial RPM release
