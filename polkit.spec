# Only enable if using patches that touches configure.ac,
# Makefile.am or other build system related files
#
%define enable_autoreconf 1

Summary: An authorization framework
Name: polkit
Version: 0.112
Release: 18%{?dist}.1
License: LGPLv2+
URL: http://www.freedesktop.org/wiki/Software/polkit
Source0: http://www.freedesktop.org/software/polkit/releases/%{name}-%{version}.tar.gz
Source1: http://www.freedesktop.org/software/polkit/releases/%{name}-%{version}.tar.gz.sign
# https://bugs.freedesktop.org/show_bug.cgi?id=71894
Patch0: polkit-0.112-XDG_RUNTIME_DIR.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=60847
Patch1: polkit-0.112-PolkitAgentSession-race.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=69501
Patch2: polkit-0.112-CVE-2015-3256.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=88288
Patch3: polkit-0.112-EnumerateActions-leak.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=72426
Patch4: polkit-0.112-Polkit.spawn-leak.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=99741
Patch5: polkit-0.112-agent-leaks.patch
# https://bugs.freedesktop.org/show_bug.cgi?id=99741
Patch6: polkit-0.112-polkitpermission-leak.patch
Patch7: polkit-0.112-add-its-files.patch
Patch8: polkit-0.112-spawning-zombie-processes.patch
Patch9: polkit-0.112-bus-conn-msg-ssh.patch
Patch10: polkit-0.112-pkttyagent-auth-errmsg-debug.patch
Patch11: polkit-0.112-CVE-2019-6133.patch

Group: System Environment/Libraries
BuildRequires: glib2-devel >= 2.30.0
BuildRequires: expat-devel
BuildRequires: pam-devel
BuildRequires: gtk-doc
BuildRequires: intltool
BuildRequires: gobject-introspection-devel
BuildRequires: systemd-devel
BuildRequires: mozjs17-devel

%if 0%{?enable_autoreconf}
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
%endif

Requires: dbus, polkit-pkla-compat

Requires(pre): shadow-utils
Requires(post): /sbin/ldconfig, systemd
Requires(preun): systemd
Requires(postun): /sbin/ldconfig, systemd

Obsoletes: PolicyKit <= 0.10
Provides: PolicyKit = 0.11

# polkit saw some API/ABI changes from 0.96 to 0.97 so require a
# sufficiently new polkit-gnome package
Conflicts: polkit-gnome < 0.97

Obsoletes: polkit-desktop-policy < 0.103
Provides: polkit-desktop-policy = 0.103

Obsoletes: polkit-js-engine < 0.110-4
Provides: polkit-js-engine = %{version}-%{release}

%description
polkit is a toolkit for defining and handling authorizations.  It is
used for allowing unprivileged processes to speak to privileged
processes.

%package devel
Summary: Development files for polkit
Group: Development/Libraries
Requires: %name = %{version}-%{release}
Requires: %name-docs = %{version}-%{release}
Requires: glib2-devel
Obsoletes: PolicyKit-devel <= 0.10
Provides: PolicyKit-devel = 0.11

%description devel
Development files for polkit.

%package docs
Summary: Development documentation for polkit
Group: Development/Libraries
Requires: %name-devel = %{version}-%{release}
Obsoletes: PolicyKit-docs <= 0.10
Provides: PolicyKit-docs = 0.11
BuildArch: noarch

%description docs
Development documentation for polkit.

%prep
%setup -q
%patch0 -p1 -b .XDG_RUNTIME_DIR
%patch1 -p1 -b .PolkitAgentSession-race
%patch2 -p1 -b .CVE-2015-3256
%patch3 -p1 -b .EnumerateActions-leak
%patch4 -p1 -b .Polkit.spawn-leak
%patch5 -p1 -b .agent-leaks
%patch6 -p1 -b .polkitpermission-leak.patch
%patch7 -p1 -b .its-files.patch
%patch8 -p1
%patch9 -p1
%patch10 -p1
%patch11 -p1

%build
%if 0%{?enable_autoreconf}
autoreconf
%endif
# we can't use _hardened_build here, see
# https://bugzilla.redhat.com/show_bug.cgi?id=962005
export CFLAGS='-fPIC %optflags'
export LDFLAGS='-pie -Wl,-z,now -Wl,-z,relro'
%configure --enable-gtk-doc \
        --disable-static \
        --enable-introspection \
        --disable-examples \
        --enable-libsystemd-login=yes --with-mozjs=mozjs-17.0
make V=1

%install
make install DESTDIR=$RPM_BUILD_ROOT INSTALL='install -p'

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

%find_lang polkit-1

%pre
getent group polkitd >/dev/null || groupadd -r polkitd
getent passwd polkitd >/dev/null || useradd -r -g polkitd -d / -s /sbin/nologin -c "User for polkitd" polkitd
exit 0

%post
/sbin/ldconfig
# The implied (systemctl preset) will fail and complain, but the macro hides
# and ignores the fact.  This is in fact what we want, polkit.service does not
# have an [Install] section and it is always started on demand.
%systemd_post polkit.service
# Restart snould usually be done in %%postun, but that wasn’t the case with
# polkit-0.112-5 and earlier. This is a workaround to ensure restarting on
# upgrades from earlier versions.
if [ $1 -gt 1 ]; then
    /usr/bin/systemctl try-restart polkit.service >/dev/null 2>&1 || :
fi

%preun
%systemd_preun polkit.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart polkit.service

%files -f polkit-1.lang
%defattr(-,root,root,-)
%doc COPYING NEWS README
%{_libdir}/lib*.so.*
%{_datadir}/man/man1/*
%{_datadir}/man/man8/*
%{_datadir}/dbus-1/system-services/*
%{_unitdir}/polkit.service
%dir %{_datadir}/polkit-1/
%dir %{_datadir}/polkit-1/actions
%attr(0700,polkitd,root) %dir %{_datadir}/polkit-1/rules.d
%{_datadir}/polkit-1/actions/org.freedesktop.policykit.policy
%dir %{_sysconfdir}/polkit-1
%{_sysconfdir}/polkit-1/rules.d/50-default.rules
%attr(0700,polkitd,root) %dir %{_sysconfdir}/polkit-1/rules.d
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.PolicyKit1.conf
%{_sysconfdir}/pam.d/polkit-1
%{_bindir}/pkaction
%{_bindir}/pkcheck
%{_bindir}/pkttyagent
%dir %{_prefix}/lib/polkit-1
%{_prefix}/lib/polkit-1/polkitd
%{_libdir}/girepository-1.0/*.typelib

# see upstream docs for why these permissions are necessary
%attr(4755,root,root) %{_bindir}/pkexec
%attr(4755,root,root) %{_prefix}/lib/polkit-1/polkit-agent-helper-1

%files devel
%defattr(-,root,root,-)
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_datadir}/gir-1.0/*.gir
%{_includedir}/*
%{_datadir}/gettext/its/polkit.its
%{_datadir}/gettext/its/polkit.loc

%files docs
%defattr(-,root,root,-)
%{_datadir}/gtk-doc

%changelog
* Tue Jan 22 2019 Jan Rybar <jrybar@redhat.com> - 0.112-18.el7_6.1
- Fix of CVE-2019-6133, PID reuse via slow fork
- Resolves: rhbz#1667311

* Wed Aug 01 2018 Jan Rybar <jrybar@redhat.com> - 0.112-18
- Error message about getting authority is too elaborate
- Resolves: rhbz#1342855

* Tue Jul 24 2018 Jan Rybar <jrybar@redhat.com> - 0.112-17
- Bus disconnection report moved to debug mode
- Resolves: rhbz#1249627

* Mon Jul 23 2018 Jan Rybar <jrybar@redhat.com> - 0.112-16
- polkit spawns zombie processes
- Authored by kwalker@redhat.com
- Resolves: rhbz#1570907

* Thu May 31 2018 Jan Rybar <jrybar@redhat.com> - 0.112-15
- Localization *its* files required by newest Gnome Shell packages
- Resolves: rhbz#1584533

* Tue Sep 19 2017 Yaakov Selkowitz <yselkowi@redhat.com> - 0.112-14
- Rebuilt for mozjs17 48-bit VA on aarch64
  Resolves: #1436518

* Tue Apr 4 2017 Miloslav Trmač <mitr@redhat.com> - 0.112-12
- Fix a memory leak in PolkitPermission.
  Patch by Rui Matos <tiagomatos@gmail.com>
  Resolves: #1433915

* Thu Feb 9 2017 Miloslav Trmač <mitr@redhat.com> - 0.112-11
- Fix memory leaks when calling authentication agents
  Resolves: #1380166

* Thu Feb 2 2017 Miloslav Trmač <mitr@redhat.com> - 0.112-10
- Fix a memory leak in Polkit.spawn calls from authorization rules
  Resolves: #1380166

* Wed Jul 6 2016 Miloslav Trmač <mitr@redhat.com> - 0.112-9
- Update for another mozjs17 change, the pkg-config file name does not change.
  Resolves: #1331776

* Mon Jul 4 2016 Miloslav Trmač <mitr@redhat.com> - 0.112-8
- Update for ABI change needed to fix use of 48-bit pointers on ARM64.
  Resolves: #1331776

* Tue May 17 2016 Miloslav Trmač <mitr@redhat.com> - 0.112-7
- Fix a memory leak when processing the result of EnumerateActions
  Resolves: #1310738

* Mon Oct 19 2015 Miloslav Trmač <mitr@redhat.com> - 0.112-6
- Fix CVE-2015-3256
  Resolves: #1271790

* Mon Feb 10 2014 Miloslav Trmač <mitr@redhat.com> - 0.112-5
- Fix a PolkitAgentSession race condition
  Resolves: #1063193

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.112-4
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.112-3
- Mass rebuild 2013-12-27

* Sat Dec  7 2013 Miloslav Trmač <mitr@redhat.com> - 0.112-2
- Workaround pam_systemd setting broken XDG_RUNTIME_DIR
  Resolves: #1033774
- Always use mozjs-17.0 even if js-devel is installed

* Wed Sep 18 2013 Miloslav Trmač <mitr@redhat.com> - 0.112-1
- Update to polkit-0.112
- Resolves: #1005135, CVE-2013-4288

* Wed May 29 2013 Tomas Bzatek <tbzatek@redhat.com> - 0.111-2
- Fix a race on PolkitSubject type registration (#866718)

* Wed May 15 2013 Miloslav Trmač <mitr@redhat.com> - 0.111-1
- Update to polkit-0.111
  Resolves: #917888
- Use SpiderMonkey from mozjs17 instead of js
- Ship the signature in the srpm
- Try to preserve timestamps in (make install)

* Fri May 10 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-4
- Shut up rpmlint about Summary:
- Build with V=1
- Use %%{_unitdir} instead of hard-coding the path
- Use the new systemd macros, primarily to run (systemctl daemon-reload)
  Resolves: #857382

* Fri May 10 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-4
- Make the JavaScript engine mandatory.  The polkit-js-engine package has been
  removed, main polkit package Provides:polkit-js-engine for compatibility.
- Add Requires: polkit-pkla-compat
  Resolves: #908808

* Wed Feb 13 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-3
- Don't ship pk-example-frobnicate in the "live" configuration
  Resolves: #878112

* Fri Feb  8 2013 Miloslav Trmač <mitr@redhat.com> - 0.110-2
- Own %%{_docdir}/polkit-js-engine-*
  Resolves: #907668

* Wed Jan  9 2013 David Zeuthen <davidz@redhat.com> - 0.110-1%{?dist}
- Update to upstream release 0.110

* Mon Jan  7 2013 Matthias Clasen <mclasen@redhat.com> - 0.109-2%{?dist}
- Build with pie and stuff

* Wed Dec 19 2012 David Zeuthen <davidz@redhat.com> 0.109-1%{?dist}
- Update to upstream release 0.109
- Drop upstreamed patches

* Thu Nov 15 2012 David Zeuthen <davidz@redhat.com> 0.108-3%{?dist}
- Attempt to open the correct libmozjs185 library, otherwise polkit
  authz rules will not work unless js-devel is installed (fdo #57146)

* Wed Nov 14 2012 David Zeuthen <davidz@redhat.com> 0.108-2%{?dist}
- Include gmodule-2.0 to avoid build error

* Wed Nov 14 2012 David Zeuthen <davidz@redhat.com> 0.108-1%{?dist}
- Update to upstream release 0.108
- Drop upstreamed patches
- This release dynamically loads the JavaScript interpreter and can
  cope with it not being available. In this case, polkit authorization
  rules are not processed and the defaults for an action - as defined
  in its .policy file - are used for authorization decisions.
- Add new meta-package, polkit-js-engine, that pulls in the required
  JavaScript bits to make polkit authorization rules work. The default
  install - not the minimal install - should include this package

* Wed Oct 10 2012 Adam Jackson <ajax@redhat.com> 0.107-4
- Don't crash if initializing the server object fails

* Tue Sep 18 2012 David Zeuthen <davidz@redhat.com> 0.107-3%{?dist}
- Authenticate as root if e.g. the wheel group is empty (#834494)

* Fri Jul 27 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.107-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jul 11 2012 David Zeuthen <davidz@redhat.com> 0.107-1%{?dist}
- Update to upstream release 0.107

* Fri Jun 29 2012 David Zeuthen <davidz@redhat.com> 0.106-2%{?dist}
- Add forgotten Requires(pre): shadow-utils

* Thu Jun 07 2012 David Zeuthen <davidz@redhat.com> 0.106-1%{?dist}
- Update to upstream release 0.106
- Authorizations are no longer controlled by .pkla files - from now
  on, use the new .rules files described in the polkit(8) man page

* Tue Apr 24 2012 David Zeuthen <davidz@redhat.com> 0.105-1%{?dist}
- Update to upstream release 0.105
- Nuke patches that are now upstream
- Change 'PolicyKit' to 'polkit' in summary and descriptions

* Thu Mar 08 2012 David Zeuthen <davidz@redhat.com> 0.104-6%{?dist}
- Don't leak file descriptors (bgo #671486)

* Mon Feb 13 2012 Matthias Clasen <mclasen@redhat.com> - 0.104-5%{?dist}
- Make the -docs subpackage noarch

* Mon Feb 06 2012 David Zeuthen <davidz@redhat.com> 0.104-4%{?dist}
- Set error if we cannot obtain a PolkitUnixSession for a given PID (#787222)

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.104-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Jan 03 2012 David Zeuthen <davidz@redhat.com> 0.104-2%{?dist}
- Nuke the ConsoleKit run-time requirement

* Tue Jan 03 2012 David Zeuthen <davidz@redhat.com> 0.104-1%{?dist}
- Update to upstream release 0.104
- Force usage of systemd (instead of ConsoleKit) for session tracking

* Tue Dec 06 2011 David Zeuthen <davidz@redhat.com> 0.103-1%{?dist}
- Update to upstream release 0.103
- Drop upstreamed patch
- Drop Fedora-specific policy, it is now upstream (fdo #41008)

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.102-3
- Rebuilt for glibc bug#747377

* Tue Oct 18 2011 David Zeuthen <davidz@redhat.com> 0.102-2%{?dist}
- Add patch to neuter the annoying systemd behavior where stdout/stderr
  is sent to the system logs

* Thu Aug 04 2011 David Zeuthen <davidz@redhat.com> 0.102-1
- Update to 0.102 release

* Fri May 13 2011 Bastien Nocera <bnocera@redhat.com> 0.101-7
- Allow setting the pretty hostname without a password for wheel,
  change matches systemd in git

* Mon May  2 2011 Matthias Clasen <mclasen@redhat.com> - 0.101-6
- Update the action id of the datetime mechanism

* Tue Apr 19 2011 David Zeuthen <davidz@redhat.com> - 0.101-5
- CVE-2011-1485 (#697951)

* Tue Mar 22 2011 Kevin Kofler <Kevin@tigcc.ticalc.org> - 0.101-4
- Also allow org.kde.kcontrol.kcmclock.save without password for wheel

* Thu Mar 17 2011 David Zeuthen <davidz@redhat.com> - 0.101-3
- Fix typo in pkla file (thanks notting)

* Thu Mar 17 2011 David Zeuthen <davidz@redhat.com> - 0.101-2
- Nuke desktop_admin_r and desktop_user_r groups - just use the
  wheel group instead (#688363)
- Update the set of configuration directives that gives users
  in the wheel group extra privileges

* Thu Mar 03 2011 David Zeuthen <davidz@redhat.com> - 0.101-1
- New upstream version

* Mon Feb 21 2011 David Zeuthen <davidz@redhat.com> - 0.100-1
- New upstream version

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan 28 2011 Matthias Clasen <mclasen@redhat.com> - 0.98-6
- Own /usr/libexec/polkit-1

* Fri Nov 12 2010 Matthias Clasen <mclasen@redhat.com> - 0.98-5
- Enable introspection

* Thu Sep 02 2010 David Zeuthen <davidz@redhat.com> - 0.98-4
- Fix #629515 in a way that doesn't require autoreconf

* Thu Sep 02 2010 David Zeuthen <davidz@redhat.com> - 0.98-2
- Include polkitagentenumtypes.h (#629515)

* Mon Aug 23 2010 Matthias Clasen <mclasen@redhat.com> - 0.98-1
- Update to upstream release 0.98
- Co-own /usr/share/gtk-doc (#604410)

* Wed Aug 18 2010 Matthias Clasen <mclasen@redhat.com> - 0.97-5
- Rebuid to work around bodhi limitations

* Wed Aug 18 2010 Matthias Clasen <mclasen@redhat.com> - 0.97-4
- Fix a ConsoleKit interaction bug

* Fri Aug 13 2010 David Zeuthen <davidz@redhat.com> - 0.97-3
- Add a patch to make pkcheck(1) work the way libvirtd uses it (#623257)
- Require GLib >= 2.25.12 instead of 2.25.11
- Ensure polkit-gnome packages earlier than 0.97 are not used with
  these packages

* Mon Aug 09 2010 David Zeuthen <davidz@redhat.com> - 0.97-2
- Rebuild

* Mon Aug 09 2010 David Zeuthen <davidz@redhat.com> - 0.97-1
- Update to 0.97. This release contains a port from EggDBus to the
  GDBus code available in recent GLib releases.

* Fri Jan 15 2010 David Zeuthen <davidz@redhat.com> - 0.96-1
- Update to 0.96
- Disable introspection support for the time being

* Fri Nov 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-2
- Rebuild

* Fri Nov 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-1
- Update to 0.95
- Drop upstreamed patches

* Tue Oct 20 2009 Matthias Clasen <mclasen@redhat.com> - 0.95-0.git20090913.3
- Fix a typo in pklocalauthority(8)

* Mon Sep 14 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913.2
- Refine how Obsolete: is used and also add Provides: (thanks Jesse
  Keating and nim-nim)

* Mon Sep 14 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913.1
- Add bugfix for polkit_unix_process_new_full() (thanks Bastien Nocera)
- Obsolete old PolicyKit packages

* Sun Sep 13 2009 David Zeuthen <davidz@redhat.com> - 0.95-0.git20090913
- Update to git snapshot
- Drop upstreamed patches
- Turn on GObject introspection
- Don't delete desktop_admin_r and desktop_user_r groups when
  uninstalling polkit-desktop-policy

* Fri Sep 11 2009 David Zeuthen <davidz@redhat.com> - 0.94-4
- Add some patches from git master
- Sort pkaction(1) output
- Bug 23867 – UnixProcess vs. SystemBusName aliasing

* Thu Aug 13 2009 David Zeuthen <davidz@redhat.com> - 0.94-3
- Add desktop_admin_r and desktop_user_r groups along with a first cut
  of default authorizations for users in these groups.

* Wed Aug 12 2009 David Zeuthen <davidz@redhat.com> - 0.94-2
- Disable GObject Introspection for now as it breaks the build

* Wed Aug 12 2009 David Zeuthen <davidz@redhat.com> - 0.94-1
- Update to upstream release 0.94

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.93-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul 20 2009 David Zeuthen <davidz@redhat.com> - 0.93-2
- Rebuild

* Mon Jul 20 2009 David Zeuthen <davidz@redhat.com> - 0.93-1
- Update to 0.93

* Tue Jun 09 2009 David Zeuthen <davidz@redhat.com> - 0.92-3
- Don't make docs noarch (I *heart* multilib)
- Change license to LGPLv2+

* Mon Jun 08 2009 David Zeuthen <davidz@redhat.com> - 0.92-2
- Rebuild

* Mon Jun 08 2009 David Zeuthen <davidz@redhat.com> - 0.92-1
- Update to 0.92 release

* Wed May 27 2009 David Zeuthen <davidz@redhat.com> - 0.92-0.git20090527
- Update to 0.92 snapshot

* Mon Feb  9 2009 David Zeuthen <davidz@redhat.com> - 0.91-1
- Initial spec file.
