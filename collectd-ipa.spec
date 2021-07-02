%global srcname collectd-ipa

Name:           %{srcname}
Version:        1.0.0
Release:        1%{?dist}
Summary:        A collectd plugin to collect statistics from IPA

License:        LGPLv3+
URL:            https://github.com/fedora-infra/collectd-ipa
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
BuildArch:      noarch

%description
%{summary}.


%package -n     python3-%{srcname}
Summary:        %{summary}

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       collectd
Requires:       collectd-python
Requires:       %{srcname}-data = %{version}-%{release}
%{?python_provide:%python_provide python3-%{srcname}}
#%%py_provides python3-%{srcname}

%description -n python3-%{srcname}
%{summary}.


%package -n %{srcname}-data
Summary:        Data files for %{name}
Requires:       collectd

%description -n %{srcname}-data
Data files (TypesDB) for %{name}.


%prep
%autosetup


%build
%py3_build

%install
%py3_install
make install INSTALL_ROOT=%{buildroot}


%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/collectd_ipa
%{python3_sitelib}/collectd_ipa-%{version}-py?.?.egg-info
%config(noreplace) %{_sysconfdir}/collectd.d/ipa.conf

%files -n %{srcname}-data
%license LICENSE
%doc README.md
%doc collection.conf
%{_datadir}/collectd/ipa-types.db
%config(noreplace) %{_sysconfdir}/collectd.d/ipa-data.conf


%changelog
* Fri Jul 02 2021 Aurelien Bompard <abompard@fedoraproject.org> - 1.0.0-1
- Initial package.
