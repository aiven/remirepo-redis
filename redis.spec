# remirepo spec file for redis, from:
#
# Fedora spec file for redis
#
# License: MIT
# http://opensource.org/licenses/MIT
#
# Please preserve changelog entries
#
%global _hardened_build 1

%if 0%{?fedora} >= 29
%global with_jemalloc 1
%else
%global with_jemalloc 0
%endif

%if 0%{?fedora} >= 19 || 0%{?rhel} >= 7
%global with_redistrib 1
%else
%global with_redistrib 0
%endif

%if 0%{?fedora} >= 19 || 0%{?rhel} >= 7
%global with_systemd 1
%else
%global with_systemd 0
%endif

# Tests fail in mock, not in local build.
%global with_tests %{?_with_tests:1}%{!?_with_tests:0}

# Pre-version are only available in github
%global upstream_ver 5.0.0
%global upstream_pre RC5
%global gh_commit    a72af0eac6d078e1062ae8a637f7d686092de102
%global gh_short     %(c=%{gh_commit}; echo ${c:0:7})
%global gh_owner     antirez
%global gh_project   redis

# Commit IDs for the (unversioned) redis-doc repository
# https://fedoraproject.org/wiki/Packaging:SourceURL "Commit Revision"
# https://github.com/antirez/redis-doc/commits/master
%global doc_commit b9d39b104e0beff9e70b3d738c17d48491d6646a
%global short_doc_commit %(c=%{doc_commit}; echo ${c:0:7})

# %%{rpmmacrodir} not usable on EL-6
%global macrosdir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

Name:              redis
Version:           %{upstream_ver}%{?upstream_pre:~%{upstream_pre}}
Release:           1%{?dist}
Summary:           A persistent key-value database
Group:             Applications/Databases
License:           BSD
URL:               http://redis.io
%if 0%{?upstream_pre:1}
Source0:           https://github.com/%{gh_owner}/%{gh_project}/archive/%{gh_commit}/%{name}-%{upstream_ver}%{upstream_pre}-%{gh_short}.tar.gz
%else
Source0:           http://download.redis.io/releases/%{name}-%{version}.tar.gz
%endif
Source1:           %{name}.logrotate
Source2:           %{name}-sentinel.service
Source3:           %{name}.service
Source4:           %{name}-sentinel.init
Source5:           %{name}.init
Source6:           %{name}-shutdown
Source7:           %{name}-limit-systemd
Source8:           %{name}-limit-init
Source9:           macros.%{name}
Source10:          https://github.com/antirez/%{name}-doc/archive/%{doc_commit}/%{name}-doc-%{short_doc_commit}.tar.gz

# To refresh patches:
# tar xf redis-xxx.tar.gz && cd redis-xxx && git init && git add . && git commit -m "%%{version} baseline"
# git am %%{patches}
# Then refresh your patches
# git format-patch HEAD~<number of expected patches>
# Update configuration for Fedora
# https://github.com/antirez/redis/pull/3491 - man pages
Patch0001:         0001-1st-man-pageis-for-redis-cli-redis-benchmark-redis-c.patch
# https://github.com/antirez/redis/pull/3494 - symlink
Patch0002:         0002-install-redis-check-rdb-as-a-symlink-instead-of-dupl.patch

BuildRequires:     gcc
%if %{?with_jemalloc}
BuildRequires:     jemalloc-devel
%else
Provides:          bundled(jemalloc) = 5.1.0
%endif
%if 0%{?with_tests}
BuildRequires:     procps-ng
BuildRequires:     tcl
%endif
%if 0%{?with_systemd}
BuildRequires:     systemd
%endif
# Required for redis-shutdown
Requires:          /bin/awk
Requires:          logrotate
Requires(pre):     shadow-utils
%if 0%{?with_systemd}
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd
%else
Requires(post):    chkconfig
Requires(preun):   chkconfig
Requires(preun):   initscripts
Requires(postun):  initscripts
%endif
Provides:          bundled(hiredis)
Provides:          bundled(lua-libs)
Provides:          bundled(linenoise)
Provides:          bundled(lzf)

%global redis_modules_abi 1
%global redis_modules_dir %{_libdir}/%{name}/modules
Provides:          redis(modules_abi)%{?_isa} = %{redis_modules_abi}

%description
Redis is an advanced key-value store. It is often referred to as a data 
structure server since keys can contain strings, hashes, lists, sets and 
sorted sets.

You can run atomic operations on these types, like appending to a string;
incrementing the value in a hash; pushing to a list; computing set 
intersection, union and difference; or getting the member with highest 
ranking in a sorted set.

In order to achieve its outstanding performance, Redis works with an 
in-memory dataset. Depending on your use case, you can persist it either 
by dumping the dataset to disk every once in a while, or by appending 
each command to a log.

Redis also supports trivial-to-setup master-slave replication, with very 
fast non-blocking first synchronization, auto-reconnection on net split 
and so forth.

Other features include Transactions, Pub/Sub, Lua scripting, Keys with a 
limited time-to-live, and configuration settings to make Redis behave like 
a cache.

You can use Redis from most programming languages also.

%package           devel
Summary:           Development header for Redis module development
# Header-Only Library (https://fedoraproject.org/wiki/Packaging:Guidelines)
Provides:          %{name}-static = %{version}-%{release}

%description       devel
Header file required for building loadable Redis modules. Detailed
API documentation is available in the redis-doc package.

%package           doc
Summary:           Documentation for Redis including man pages
License:           CC-BY-SA
BuildArch:         noarch

# http://fedoraproject.org/wiki/Packaging:Conflicts "Splitting Packages"
Conflicts:         redis < 4.0

%description       doc
Manual pages and detailed documentation for many aspects of Redis use,
administration and development.

%if 0%{?with_redistrib}
%package           trib
Summary:           Cluster management script for Redis
BuildArch:         noarch
Requires:          ruby
Requires:          rubygem-redis

%description       trib
Redis cluster management utility providing cluster creation, node addition
and removal, status checks, resharding, rebalancing, and other operations.
%endif

%prep
%if 0%{?upstream_pre:1}
%setup -q -n %{gh_project}-%{gh_commit} -b 10
%else
%setup -q -b 10
%endif
mv ../%{name}-doc-%{doc_commit} doc
%patch0001 -p1
%patch0002 -p1

%if %{?with_jemalloc}
rm -frv deps/jemalloc
# Use system jemalloc library
sed -i -e '/cd jemalloc && /d' deps/Makefile
sed -i -e 's|../deps/jemalloc/lib/libjemalloc.a|-ljemalloc -ldl|g' src/Makefile
sed -i -e 's|-I../deps/jemalloc.*|-DJEMALLOC_NO_DEMANGLE -I/usr/include/jemalloc|g' src/Makefile
%else
mv deps/jemalloc/COPYING COPYING-jemalloc
%endif
mv deps/lua/COPYRIGHT    COPYRIGHT-lua
mv deps/hiredis/COPYING  COPYING-hiredis

# Configuration file changes and additions
sed -i -e 's|^logfile .*$|logfile /var/log/redis/redis.log|g' redis.conf
sed -i -e '$ alogfile /var/log/redis/sentinel.log' sentinel.conf
sed -i -e 's|^dir .*$|dir /var/lib/redis|g' redis.conf

# Module API version safety check
api=`sed -n -e 's/#define REDISMODULE_APIVER_[0-9][0-9]* //p' src/redismodule.h`
if test "$api" != "%{redis_modules_abi}"; then
   : Error: Upstream API version is now ${api}, expecting %%{redis_modules_abi}.
   : Update the redis_modules_abi macro, the rpmmacros file, and rebuild.
   exit 1
fi

# Fix for old GCC
%if 0%{?rhel} == 6
sed -e '/GCC diagnostic/d' -i src/lzf_d.c
%endif

%global malloc_flags	MALLOC=jemalloc
%global make_flags	DEBUG="" V="echo" LDFLAGS="%{?__global_ldflags}" CFLAGS+="%{optflags} -fPIC" %{malloc_flags} INSTALL="install -p" PREFIX=%{buildroot}%{_prefix}

%build
make %{?_smp_mflags} %{make_flags} all

%install
make %{make_flags} install

# Filesystem.
install -d %{buildroot}%{_sharedstatedir}/%{name}
install -d %{buildroot}%{_localstatedir}/log/%{name}
install -d %{buildroot}%{_localstatedir}/run/%{name}
install -d %{buildroot}%{redis_modules_dir}

# Install logrotate file.
install -pDm644 %{S:1} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# Install configuration files.
install -pDm640 %{name}.conf %{buildroot}%{_sysconfdir}/%{name}.conf
install -pDm640 sentinel.conf %{buildroot}%{_sysconfdir}/%{name}-sentinel.conf

# Install systemd unit files.
%if 0%{?with_systemd}
mkdir -p %{buildroot}%{_unitdir}
install -pm644 %{S:3} %{buildroot}%{_unitdir}
install -pm644 %{S:2} %{buildroot}%{_unitdir}

# Install systemd limit files (requires systemd >= 204)
install -p -D -m 644 %{S:7} %{buildroot}%{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
install -p -D -m 644 %{S:7} %{buildroot}%{_sysconfdir}/systemd/system/%{name}-sentinel.service.d/limit.conf
%else # install SysV service files
install -pDm755 %{S:4} %{buildroot}%{_initrddir}/%{name}-sentinel
install -pDm755 %{S:5} %{buildroot}%{_initrddir}/%{name}
install -p -D -m 644 %{S:8} %{buildroot}%{_sysconfdir}/security/limits.d/95-%{name}.conf
%endif

# Fix non-standard-executable-perm error.
chmod 755 %{buildroot}%{_bindir}/%{name}-*

# Install redis-shutdown
install -pDm755 %{S:6} %{buildroot}%{_libexecdir}/%{name}-shutdown

# Install redis module header
install -pDm644 src/%{name}module.h %{buildroot}%{_includedir}/%{name}module.h

%if 0%{?with_redistrib}
# Install redis-trib
install -pDm755 src/%{name}-trib.rb %{buildroot}%{_bindir}/%{name}-trib
%endif

# Install man pages
man=$(dirname %{buildroot}%{_mandir})
for page in man/man?/*; do
    install -Dpm644 $page $man/$page
done
ln -s redis-server.1 %{buildroot}%{_mandir}/man1/redis-sentinel.1
ln -s redis.conf.5   %{buildroot}%{_mandir}/man5/redis-sentinel.conf.5

# Install documentation and html pages
doc=$(echo %{buildroot}/%{_docdir}/%{name})
for page in 00-RELEASENOTES BUGS CONTRIBUTING MANIFESTO; do
    install -Dpm644 $page $doc/$page
done
for page in $(find doc -name \*.md | sed -e 's|.md$||g'); do
    base=$(echo $page | sed -e 's|doc/||g')
    install -Dpm644 $page.md $doc/$base.md
done

# Install rpm macros for redis modules
mkdir -p %{buildroot}%{macrosdir}
install -pDm644 %{S:9} %{buildroot}%{macrosdir}/macros.%{name}

%check
%if 0%{?with_tests}
%if ! %{?with_jemalloc}
# ERR Active defragmentation cannot be enabled: it requires a Redis server compiled
# with a modified Jemalloc like the one shipped by default with the Redis source distribution
sed -e '/memefficiency/d' -i tests/test_helper.tcl
%endif

# https://github.com/antirez/redis/issues/1417 (for "taskset -c 1")
taskset -c 1 make %{make_flags} test
make %{make_flags} test-sentinel
%else
: Test disabled, missing '--with tests' option.
%endif

%pre
getent group %{name} &> /dev/null || \
groupadd -r %{name} &> /dev/null
getent passwd %{name} &> /dev/null || \
useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
-c 'Redis Database Server' %{name} &> /dev/null
exit 0

%post
%if 0%{?with_systemd}
%systemd_post %{name}.service
%systemd_post %{name}-sentinel.service
%else
chkconfig --add %{name}
chkconfig --add %{name}-sentinel
%endif

%preun
%if 0%{?with_systemd}
%systemd_preun %{name}.service
%systemd_preun %{name}-sentinel.service
%else
if [ $1 -eq 0 ] ; then
    service %{name} stop &> /dev/null
    chkconfig --del %{name} &> /dev/null
    service %{name}-sentinel stop &> /dev/null
    chkconfig --del %{name}-sentinel &> /dev/null
fi
%endif

%postun
%if 0%{?with_systemd}
%systemd_postun_with_restart %{name}.service
%systemd_postun_with_restart %{name}-sentinel.service
%else
if [ "$1" -ge "1" ] ; then
    service %{name} condrestart >/dev/null 2>&1 || :
    service %{name}-sentinel condrestart >/dev/null 2>&1 || :
fi
%endif

%files
%{!?_licensedir:%global license %%doc}
%license COPYING
%license COPYRIGHT-lua
%license COPYING-hiredis
%if ! %{?with_jemalloc}
%license COPYING-jemalloc
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0640, redis, root) %config(noreplace) %{_sysconfdir}/%{name}.conf
%attr(0640, redis, root) %config(noreplace) %{_sysconfdir}/%{name}-sentinel.conf
%dir %attr(0750, redis, redis) %{_libdir}/%{name}
%dir %attr(0750, redis, redis) %{redis_modules_dir}
%dir %attr(0750, redis, redis) %{_sharedstatedir}/%{name}
%dir %attr(0750, redis, redis) %{_localstatedir}/log/%{name}
%if 0%{?with_redistrib}
%exclude %{_bindir}/%{name}-trib
%endif
%exclude %{macrosdir}
%exclude %{_includedir}
%exclude %{_docdir}/%{name}/*
%{_bindir}/%{name}-*
%{_libexecdir}/%{name}-*
%{_mandir}/man1/%{name}*
%{_mandir}/man5/%{name}*
%if 0%{?with_systemd}
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-sentinel.service
%dir %{_sysconfdir}/systemd/system/%{name}.service.d
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
%dir %{_sysconfdir}/systemd/system/%{name}-sentinel.service.d
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}-sentinel.service.d/limit.conf
%dir %attr(0755, redis, redis) %ghost %{_localstatedir}/run/%{name}
%else
%{_initrddir}/%{name}
%{_initrddir}/%{name}-sentinel
%config(noreplace) %{_sysconfdir}/security/limits.d/95-%{name}.conf
%dir %attr(0755, redis, redis) %{_localstatedir}/run/%{name}
%endif

%files devel
%license COPYING
%{_includedir}/%{name}module.h
%{macrosdir}/*

%files doc
%docdir %{_docdir}/%{name}
%{_docdir}/%{name}

%if 0%{?with_redistrib}
%files trib
%license COPYING
%{_bindir}/%{name}-trib
%endif


%changelog
* Thu Sep  6 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC5-1
- Redis 5.0 RC5 (4.9.105) - Released Thu Sep 06 12:54:29 CEST 2018

* Sun Sep  2 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC4-2
- use bunled jemalloc instead of system shared version

* Thu Aug  9 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC4-1
- Redis 5.0 RC4 (4.9.104) - Released Fri Aug 03 13:51:02 CEST 2018
- Drop the pandoc build dependency, install only markdown.

* Thu Jun 14 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC3-1
- Redis 5.0 RC3 (4.9.103) - Released Wed Jun 14 9:51:44 CEST 2018

* Thu Jun 14 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC2-1
- Redis 5.0 RC2 (4.9.102) - Released Wed Jun 13 12:49:13 CEST 2018
- Upgrade urgency CRITICAL: This release fixes important security issues.
                      HIGH: This release fixes a SCAN commands family bug.
                  MODERATE: This release fixes a PSYNC2 edge case with expires.
                  MODERATE: Sentinel related fixes.
                       LOW: All the other issues

* Wed May 30 2018 Remi Collet <remi@remirepo.net> - 5.0.0~RC1-1
- update to 5.0.0-RC1 (4.9.101)
- open https://github.com/antirez/redis/pull/4964 - stdint.h

* Mon Mar 26 2018 Remi Collet <remi@remirepo.net> - 4.0.9-1
- Update to 4.0.9 - Released Mon Mar 26 17:52:32 CEST 2018
- Upgrade urgency CRITICAL: Critical upgrade for users
  using AOF with the fsync policy set to "always".

* Sun Feb  4 2018 Remi Collet <remi@remirepo.net> - 4.0.8-1
- Update to 4.0.8 - Released Fri Feb 2 11:17:40 CET 2018
- Upgrade urgency CRITICAL ONLY for Redis Cluster users.

* Wed Jan 24 2018 Remi Collet <remi@remirepo.net> - 4.0.7-1
- Redis 4.0.7 - Released Wed Jan 24 11:01:40 CET 2018
- Upgrade urgency MODERATE: Several bugs fixed, but none of critical level.
- Update to current upstream redis-doc

* Tue Dec  5 2017 Remi Collet <remi@remirepo.net> - 4.0.6-1
- Redis 4.0.6 - Released Thu Dec 4 17:54:10 CET 2017
- Upgrade urgency CRITICAL: More errors in the fixes for PSYNC2
  in Redis 4.0.5 were identified.

* Fri Dec  1 2017 Remi Collet <remi@remirepo.net> - 4.0.5-1
- Redis 4.0.5 - Released Thu Dec 1 16:03:32 CET 2017
- Upgrade urgency CRITICAL: Redis 4.0.4 fix for PSYNC2 was broken,
  causing the slave to crash when receiving an RDB file from the
  master that contained a duplicated Lua script.

* Fri Dec 01 2017 Nathan Scott <nathans@redhat.com> - 4.0.4-1
- Upstream 4.0.4 release.
- Update to current upstream redis-doc also.
- Fix man page issues (RHBZ #1513594 and RHBZ #1515417).

* Thu Nov 30 2017 Remi Collet <remi@remirepo.net> - 4.0.3-1
- Redis 4.0.3 - Released Thu Nov 30 13:14:50 CET 2017
- Upgrade urgency CRITICAL: Several PSYNC2 bugs can corrupt the
  slave data set after a restart and a successful PSYNC2 handshake.
- drop duplicated documentation from main package

* Tue Nov 21 2017 Remi Collet <remi@remirepo.net> - 4.0.2-3
- add doc and devel subpackages, synced from Fedora
- keep man pages in main package
- minor fix for EL-6 and tests

* Tue Sep 26 2017 Remi Collet <remi@remirepo.net> - 4.0.2-2
- simplify build, synced from Fedora

* Thu Sep 21 2017 Remi Collet <remi@remirepo.net> - 4.0.2-1
- Redis 4.0.2 - Released Thu Sep 21 15:47:53 CEST 2017
- Upgrade urgency HIGH: Several potentially critical bugs fixed.

* Tue Sep  5 2017 Remi Collet <remi@remirepo.net> - 4.0.1-3
- switch systemd unit to Type=notify, see rhbz #1172841

* Fri Aug 18 2017 Remi Collet <remi@remirepo.net> - 4.0.1-2
- Add redis-trib based on patch from Sebastian Saletnik.  (RHBZ #1215654)

* Tue Aug  1 2017 Remi Collet <remi@remirepo.net> - 4.0.1-1
- Redis 4.0.1 - Released Mon Jul 24 15:51:31 CEST 2017
- Upgrade urgency MODERATE: A few serious but non critical bugs

* Mon Jul 17 2017 Remi Collet <remi@remirepo.net> - 4.0.0-1
- update to 4.0.0 GA

* Sat Jun 24 2017 Remi Collet <remi@remirepo.net> - 4.0.0-0.4.RC3
- rebuild with some fedora changes:
 - Add RuntimeDirectory=redis to systemd unit file (RHBZ #1454700)
 - Fix a shutdown failure with Unix domain sockets (RHBZ #1444988)

* Mon Apr 24 2017 Remi Collet <remi@fedoraproject.org> - 4.0.0-0.3.RC3
- update to 4.0.0-RC3 (3.9.103)

* Tue Dec  6 2016 Remi Collet <remi@fedoraproject.org> - 4.0.0-0.2.RC2
- update to 4.0.0-RC2 (3.9.102)

* Mon Dec  5 2016 Remi Collet <remi@fedoraproject.org> - 4.0.0-0.1.RC1
- update to 4.0.0-RC1 (3.9.101)

* Thu Oct 27 2016 Remi Collet <remi@fedoraproject.org> - 3.2.5-1
- Redis 3.2.5 - Released Wed Oct 26 09:16:40 CEST 2016
- Upgrade urgency LOW: This release only fixes a compilation issue

* Mon Sep 26 2016 Remi Collet <remi@fedoraproject.org> - 3.2.4-1
- Redis 3.2.4 - Released Mon Sep 26 08:58:21 CEST 2016
- Upgrade urgency CRITICAL: Redis 3.2 and unstable contained
  a security vulnerability fixed by this release.

* Wed Sep 14 2016 Remi Collet <remi@fedoraproject.org> - 3.2.3-4
- move redis-shutdown to libexec
- add missing LSB headers to init scripts

* Fri Sep  9 2016 Remi Collet <remi@fedoraproject.org> - 3.2.3-3
- add patch from https://github.com/antirez/redis/pull/3494

* Fri Sep  9 2016 Remi Collet <remi@fedoraproject.org> - 3.2.3-2
- add man pages from https://github.com/antirez/redis/pull/3491
- data and configuration should not be publicly readable
- remove /var/run/redis with systemd
- provide redis-check-rdb as a symlink to redis-server

* Tue Aug  2 2016 Remi Collet <remi@fedoraproject.org> - 3.2.3-1
- Redis 3.2.3 - Release date: Tue Aug 02 10:55:24 CEST 2016
- Upgrade urgency MODERATE: Fix replication delay and redis-cli
  security issue.

* Fri Jul 29 2016 Remi Collet <remi@fedoraproject.org> - 3.2.2-1
- Redis 3.2.2 - Release date: Thu Jul 28 14:14:54 CEST 2016
- Upgrade urgency MODERATE:
  A Redis server and a Sentinel crash are now fixed.
  GEORADIUS errors in reported entries are fixed.

* Fri Jun 24 2016 Remi Collet <remi@fedoraproject.org> - 3.2.1-2
- fix %%postun scriptlet, thanks Matthias

* Mon Jun 20 2016 Remi Collet <remi@fedoraproject.org> - 3.2.1-1
- Redis 3.2.1 - Release date: Fri Jun 17 15:01:56 CEST 2016
- Upgrade urgency HIGH: Critical fix to Redis Sentinel,
  due to 3.2.0 regression compared to 3.0.

* Tue May 10 2016 Remi Collet <remi@fedoraproject.org> - 3.2.0-1
- update to 3.2.0

* Mon Feb  8 2016 Haïkel Guémar <hguemar@fedoraproject.org> - 3.2-0.4.rc3
- Fix redis-shutdown to handle password-protected instances shutdown

* Thu Jan 28 2016 Remi Collet <remi@fedoraproject.org> - 3.2-0.3.rc3
- update to 3.2-rc3 (version 3.1.103)

* Tue Jan 26 2016 Remi Collet <remi@fedoraproject.org> - 3.2-0.2.rc2
- update to 3.2-rc2 (version 3.1.102)

* Fri Jan 15 2016 Remi Collet <remi@fedoraproject.org> - 3.2-0.1.rc1
- update to 3.2-rc1 (version 3.1.101)
  This is the first release candidate of Redis 3.2

* Sat Dec 26 2015 Remi Collet <remi@fedoraproject.org> - 3.0.6-1
- Redis 3.0.6 - Release date: 18 Dec 2015
- Upgrade urgency: MODERATE

* Fri Oct 16 2015 Remi Collet <remi@fedoraproject.org> - 3.0.5-1
- Redis 3.0.5 - Release date: 15 Oct 2015
- Upgrade urgency: MODERATE

* Thu Sep 10 2015 Remi Collet <remi@fedoraproject.org> - 3.0.4-1
- Redis 3.0.4 - Release date: 8 Sep 2015
- Upgrade urgency: HIGH for Redis and Sentinel.

* Wed Aug  5 2015 Remi Collet <remi@fedoraproject.org> - 3.0.3-1.1
- make redis-shutdown more robust, see #22

* Fri Jul 17 2015 Remi Collet <remi@fedoraproject.org> - 3.0.3-1
- Redis 3.0.3 - Release date: 17 Jul 2015
- Upgrade urgency: LOW for Redis and Sentinel.

* Tue Jun  9 2015 Remi Collet <remi@fedoraproject.org> - 3.0.2-1
- Redis 3.0.2 - Release date: 4 Jun 2015
- Upgrade urgency: HIGH for Redis because of a security issue.
                   LOW for Sentinel.

* Wed May  6 2015 Remi Collet <remi@fedoraproject.org> - 3.0.1-1
- Redis 3.0.1 - Release date: 5 May 2015
- Upgrade urgency: LOW for Redis and Cluster, MODERATE for Sentinel.

* Tue Apr 14 2015 Remi Collet <remi@fedoraproject.org> - 3.0.0-2
- rebuild with new redis-shutdown from rawhide
- improved description from rawhide
- use redis/redis owner for directories under /var

* Mon Apr  6 2015 Remi Collet <remi@fedoraproject.org> - 3.0.0-1
- Redis 3.0.0 - Release date: 1 Apr 2015

* Thu Mar 26 2015 Haïkel Guémar <hguemar@fedoraproject.org> - 2.8.19-2
- Fix redis-shutdown on multiple NIC setup (RHBZ #1201237)

* Wed Dec 17 2014 Remi Collet <remi@fedoraproject.org> - 2.8.19-1
- Redis 2.8.19 - Release date: 16 Dec 2014
  upgrade urgency: LOW for both Redis and Sentinel.

* Sat Dec 13 2014 Remi Collet <remi@fedoraproject.org> - 2.8.18-2
- provides /etc/systemd/system/redis.service.d/limit.conf
  and /etc/systemd/system/redis-sentinel.service.d/limit.conf
  or /etc/security/limits.d/95-redis.conf

* Thu Dec  4 2014 Remi Collet <remi@fedoraproject.org> - 2.8.18-1.1
- EL-5 rebuild with upstream patch

* Thu Dec  4 2014 Remi Collet <remi@fedoraproject.org> - 2.8.18-1
- Redis 2.8.18 - Release date: 4 Dec 2014
  upgrade urgency: LOW for both Redis and Sentinel.
- fix isfinite missing on EL-5

* Sun Sep 21 2014 Remi Collet <remi@fedoraproject.org> - 2.8.17-2
- fix sentinel service unit file for systemd
- also use redis-shutdown in init scripts

* Sat Sep 20 2014 Remi Collet <remi@fedoraproject.org> - 2.8.17-1
- Redis 2.8.17 - Release date: 19 Sep 2014
  upgrade urgency: HIGH for Redis Sentinel, LOW for Redis Server.

* Wed Sep 17 2014 Remi Collet <remi@fedoraproject.org> - 2.8.16-1
- Redis 2.8.16 - Release date: 16 Sep 2014
  upgrade urgency: HIGH for Redis, LOW for Sentinel.

* Fri Sep 12 2014 Remi Collet <remi@fedoraproject.org> - 2.8.15-1
- Redis 2.8.15 - Release date: 12 Sep 2014
  upgrade urgency: LOW for Redis, HIGH for Sentinel.
- move commands from /usr/sbin to /usr/bin
- add redis-shutdown command (systemd)

* Thu Sep  4 2014 Remi Collet <remi@fedoraproject.org> - 2.8.14-1
- Redis 2.8.14 - Release date:  1 Sep 2014
  upgrade urgency: HIGH for Lua scripting users, otherwise LOW.

* Tue Jul 15 2014 Remi Collet <remi@fedoraproject.org> - 2.8.13-1
- Redis 2.8.13 - Release date: 14 Jul 2014
  upgrade urgency: LOW for Redis and Sentinel

* Tue Jun 24 2014 Remi Collet <remi@fedoraproject.org> - 2.8.12-1
- Redis 2.8.12 - Release date: 23 Jun 2014
  upgrade urgency: HIGH for Redis, CRITICAL for Sentinel.
- always use jemalloc (instead of tcmalloc)

* Mon Jun 16 2014 Remi Collet <remi@fedoraproject.org> - 2.8.11-1
- Redis 2.8.11 - Release date: 11 Jun 2014
  upgrade urgency: HIGH if you use Lua scripting, LOW otherwise.

* Fri Jun  6 2014 Remi Collet <remi@fedoraproject.org> - 2.8.10-1
- Redis 2.8.10 - Release date: 5 Jun 2014
  upgrade urgency: HIGH if you use min-slaves-to-write option.

* Tue Apr 22 2014 Remi Collet <remi@fedoraproject.org> - 2.8.9-1
- Redis 2.8.9 - Release date: 22 Apr 2014
  upgrade urgency: LOW, only new features introduced, no bugs fixed.

* Thu Mar 27 2014 Remi Collet <remi@fedoraproject.org> - 2.8.8-1
- Redis 2.8.8 - Release date: 25 Mar 2014
  upgrade urgency: HIGH for Redis, LOW for Sentinel.

* Sat Mar  8 2014 Remi Collet <remi@fedoraproject.org> - 2.8.7-1
- Redis 2.8.7 - Release date: 5 Mar 2014
  upgrade urgency: LOW for Redis, LOW for Sentinel.

* Fri Feb 14 2014 Remi Collet <remi@fedoraproject.org> - 2.8.6-1
- Redis 2.8.6 - Release date: 13 Feb 2014
  upgrade urgency: HIGH for Redis, LOW for Sentinel.

* Thu Jan 16 2014 Remi Collet <remi@fedoraproject.org> - 2.8.4-1
- Redis 2.8.4 - Release date: 13 Jan 2014
  upgrade urgency: MODERATE for Redis and Sentinel.

* Mon Jan  6 2014 Remi Collet <remi@fedoraproject.org> - 2.8.3-2
- add redis-sentinel command (link to redis-server)
- don't rely on config for daemonize and pidfile
- add redis-sentinel service

* Sat Dec 14 2013 Remi Collet <remi@fedoraproject.org> - 2.8.3-1
- Redis 2.8.3
  upgrade urgency: MODERATE for Redis, HIGH for Sentinel.
- redis own /etc/redis.conf (needed CONFIG WRITE)
- add sentinel.conf as documentation

* Mon Dec  2 2013 Remi Collet <remi@fedoraproject.org> - 2.8.2-1
- Redis 2.8.2, new major version
- pull rawhide changes (add tmpfiles)

* Sun Sep  8 2013 Remi Collet <remi@fedoraproject.org> - 2.6.16-1
- Redis 2.6.16
  upgrade urgency: MODERATE

* Fri Sep 06 2013 Fabian Deutsch <fabian.deutsch@gmx.de> - 2.6.16-1
- Update to 2.6.16
- Fix rhbz#973151
- Fix rhbz#656683
- Fix rhbz#977357 (Jan Vcelak <jvcelak@fedoraproject.org>)

* Sat Aug 24 2013 Remi Collet <remi@fedoraproject.org> - 2.6.15-1
- Redis 2.6.15
  upgrade urgency: MODERATE, upgrade ASAP only if you experience
  issues related to the expired keys collection algorithm,
  or if you use the ZUNIONSTORE command.

* Sun Jul 28 2013 Remi Collet <remi@fedoraproject.org> - 2.6.14-1
- Redis 2.6.14
  upgrade urgency: HIGH because of the following two issues:
    Lua scripting + Replication + AOF in slaves problem
    AOF + expires possible race condition
- add option to run tests during build (not in mock)

* Tue Jul 23 2013 Peter Robinson <pbrobinson@fedoraproject.org> 2.6.13-4
- ARM has gperftools

* Wed Jun 19 2013 Fabian Deutsch <fabiand@fedoraproject.org> - 2.6.13-3
- Modify jemalloc patch for s390 compatibility (Thanks sharkcz)

* Fri Jun 07 2013 Fabian Deutsch <fabiand@fedoraproject.org> - 2.6.13-2
- Unbundle jemalloc

* Fri Jun 07 2013 Fabian Deutsch <fabiand@fedoraproject.org> - 2.6.13-1
- Add compile PIE flag (rhbz#955459)
- Update to redis 2.6.13 (rhbz#820919)

* Tue Apr 30 2013 Remi Collet <remi@fedoraproject.org> - 2.6.13-1
- Redis 2.6.13
  upgrade urgency: MODERATE, nothing very critical

* Sat Mar 30 2013 Remi Collet <remi@fedoraproject.org> - 2.6.12-1
- Redis 2.6.12
  upgrade urgency: MODERATE, nothing very critical
  but a few non trivial bugs

* Tue Mar 12 2013 Remi Collet <remi@fedoraproject.org> - 2.6.11-1
- Redis 2.6.11
  upgrade urgency: LOW, however updating is encouraged
  if you have many instances per server and you want
  to lower the CPU / energy usage.

* Mon Feb 11 2013 Remi Collet <remi@fedoraproject.org> - 2.6.10-1
- Redis 2.6.10
  upgrade urgency: MODERATE, this release contains many non
  critical fixes and many small improvements.

* Thu Jan 17 2013 Remi Collet <remi@fedoraproject.org> - 2.6.9-1
- Redis 2.6.9
  upgrade urgency: MODERATE if you use replication.

* Fri Jan 11 2013 Remi Collet <remi@fedoraproject.org> - 2.6.8-1
- Redis 2.6.8
  upgrade urgency: MODERATE if you use Lua scripting. Otherwise LOW.

* Tue Dec  4 2012 Remi Collet <remi@fedoraproject.org> - 2.6.7-1
- Redis 2.6.7
  upgrade urgency: MODERATE (unless you BLPOP using the same
  key multiple times).

* Fri Nov 23 2012 Remi Collet <remi@fedoraproject.org> - 2.6.5-1
- Redis 2.6.5 (upgrade urgency: moderate)

* Fri Nov 16 2012 Remi Collet <remi@fedoraproject.org> - 2.6.4-1
- Redis 2.6.4 (upgrade urgency: low)

* Sun Oct 28 2012 Remi Collet <remi@fedoraproject.org> - 2.6.2-1
- Redis 2.6.2 (upgrade urgency: low)
- fix typo in systemd macro

* Wed Oct 24 2012 Remi Collet <remi@fedoraproject.org> - 2.6.0-1
- Redis 2.6.0 is the latest stable version
- add patch for old glibc on RHEL-5

* Sat Oct 20 2012 Remi Collet <remi@fedoraproject.org> - 2.6.0-0.2.rc8
- Update to redis 2.6.0-rc8
- improve systemd integration

* Thu Aug 30 2012 Remi Collet <remi@fedoraproject.org> - 2.6.0-0.1.rc6
- Update to redis 2.6.0-rc6

* Thu Aug 30 2012 Remi Collet <remi@fedoraproject.org> - 2.4.16-1
- Update to redis 2.4.16

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.15-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jul 08 2012 Silas Sewell <silas@sewell.org> - 2.4.15-2
- Remove TODO from docs

* Sun Jul 08 2012 Silas Sewell <silas@sewell.org> - 2.4.15-1
- Update to redis 2.4.15

* Sat May 19 2012 Silas Sewell <silas@sewell.org> - 2.4.13-1
- Update to redis 2.4.13

* Sat Mar 31 2012 Silas Sewell <silas@sewell.org> - 2.4.10-1
- Update to redis 2.4.10

* Fri Feb 24 2012 Silas Sewell <silas@sewell.org> - 2.4.8-1
- Update to redis 2.4.8

* Sat Feb 04 2012 Silas Sewell <silas@sewell.org> - 2.4.7-1
- Update to redis 2.4.7

* Wed Feb 01 2012 Fabian Deutsch <fabiand@fedoraproject.org> - 2.4.6-4
- Fixed a typo in the spec

* Tue Jan 31 2012 Fabian Deutsch <fabiand@fedoraproject.org> - 2.4.6-3
- Fix .service file, to match config (Type=simple).

* Tue Jan 31 2012 Fabian Deutsch <fabiand@fedoraproject.org> - 2.4.6-2
- Fix .service file, credits go to Timon.

* Thu Jan 12 2012 Fabian Deutsch <fabiand@fedoraproject.org> - 2.4.6-1
- Update to 2.4.6
- systemd unit file added
- Compiler flags changed to compile 2.4.6
- Remove doc/ and Changelog

* Sun Jul 24 2011 Silas Sewell <silas@sewell.org> - 2.2.12-1
- Update to redis 2.2.12

* Fri May 06 2011 Dan Horák <dan[at]danny.cz> - 2.2.5-2
- google-perftools exists only on selected architectures

* Sat Apr 23 2011 Silas Sewell <silas@sewell.ch> - 2.2.5-1
- Update to redis 2.2.5

* Sat Mar 26 2011 Silas Sewell <silas@sewell.ch> - 2.2.2-1
- Update to redis 2.2.2

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Dec 19 2010 Silas Sewell <silas@sewell.ch> - 2.0.4-1
- Update to redis 2.0.4

* Tue Oct 19 2010 Silas Sewell <silas@sewell.ch> - 2.0.3-1
- Update to redis 2.0.3

* Fri Oct 08 2010 Silas Sewell <silas@sewell.ch> - 2.0.2-1
- Update to redis 2.0.2
- Disable checks section for el5

* Sat Sep 11 2010 Silas Sewell <silas@sewell.ch> - 2.0.1-1
- Update to redis 2.0.1

* Sat Sep 04 2010 Silas Sewell <silas@sewell.ch> - 2.0.0-1
- Update to redis 2.0.0

* Thu Sep 02 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-3
- Add Fedora build flags
- Send all scriplet output to /dev/null
- Remove debugging flags
- Add redis.conf check to init script

* Mon Aug 16 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-2
- Don't compress man pages
- Use patch to fix redis.conf

* Tue Jul 06 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-1
- Initial package
