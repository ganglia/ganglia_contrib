Name:           ganglia-logtailer
Version:        1.2
Release:        1%{?dist}
Summary:        Framework to crunch data from logfiles and send using gmetric.


Group:         Applications/Internet 
License:       GPL2+
URL:           http://bitbucket.org/maplebed/ganglia-logtailer/overview/
Source0:       %{name}.tar.gz 
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: python-devel
Requires:     ganglia-gmond

%description
ganglia-logtailer is a  Many metrics associated with ganglia and gmetric
plugins are rather easy to collect; you poll the relevant application for a
value and report it.  Examples are asking MySQL for the number of questions and
calculating queries per second, or asking iostat for the percentage disk I/O
currently being used.  However, there are a large number of applications out
there that don't support being queried for interesting data, but do provide a
log file which, when properly parsed, yields the interesting data we desire.
An example of the latter category is Apache, which does not furnish any
interface for measuring queries per second, yet has a log file allowing you to
count how many queries come in over a specific time period.
 
ganglia-logtailer is designed to make it easy to parse any log file, pull out
the information you desire, and plug it into ganglia to make pretty graphs.

%prep
%setup -q -n %{name}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
install -d -m 755 $RPM_BUILD_ROOT/var/lib/ganglia-logtailer
install -d -m 755 $RPM_BUILD_ROOT/var/log/ganglia-logtailer


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_sbindir}/ganglia-logtailer
%{_datadir}/%{name}
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/log/%{name}
%doc debian/README debian/BUGS debian/copyright



%changelog
* Wed Mar 20 2010 Paul Nasrat <pnasrat@googlemail.com> - 1.2-1
- Initial version
