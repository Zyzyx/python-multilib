Name:       python2-multilib
Version:    1.0
Release:    1%{?dist}
Summary:    a module for determining if a package is multilib or not
Group:      Development/Libraries
License:    GPLv3+
URL:        https://github.com/Zyzyx/python-multilib/archive/master.zip
Source0:    %{name}-%{version}.zip

BuildRequires:  python2-devel
Requires:       python2

%description
A Python module that supports several multilib "methods" useful for determining
if a 32-bit package should be included with its 64-bit analogue in a compose.

%prep
%setup -q


%build
%configure
%py2_build

%install
%py2_install


%files
%{python2-sitedir}/%{name}/*
%{_bindir}/multilib_test_data
%doc README.md LICENSE


%changelog
* Tue Jul 21 2009 Jay Greguske <jgregusk@redhat.com> - 1.0-1
- Initial RPM release
