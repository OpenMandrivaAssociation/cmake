%define shortVersion %(echo %{version} | cut -d. -f1,2)

%bcond_with bootstrap

%define beta %{nil}

Name:		cmake
Summary:	Cross-platform, open-source make system
Version:	3.13.3
%if "%{beta}" != ""
Release:	0.%{beta}.1
Source0:	http://www.cmake.org/files/v%{shortVersion}/%{name}-%{version}-%{beta}.tar.gz
%else
Release:	1
Source0:	http://www.cmake.org/files/v%{shortVersion}/%{name}-%{version}.tar.gz
%endif
Epoch:		1
License:	BSD
Group:		Development/Other
Url:		http://www.cmake.org/HTML/index.html
Source1:	cmake.macros
Source2:	https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.attr
# cmake.prov is based on Fedora's versions found at
# https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.prov
# And fixed up to handle e.g. cmake(PkgConfig) correctly.
Source3:	cmake.prov
# cmake.req is based on Fedora's versions found at
# https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.req
# And extended with a simplistic check for KDE Frameworks interdependencies
Source4:	cmake.req
Source100:	cmake.rpmlintrc
Patch1:		cmake-3.11.0-pthread-linkage.patch
Patch2:		cmake-3.9.0-clang-5.0.patch
Patch3:		cmake-3.4.1-dont-override-fPIC-with-fPIE.patch
BuildRequires:	perl
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(libidn)
BuildRequires:	pkgconfig(libuv)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	xz
BuildRequires:	pkgconfig(expat)
BuildRequires:	bzip2-devel
BuildRequires:	pkgconfig(libarchive)
%if !%{with bootstrap}
BuildRequires:	qmake5
BuildRequires:	pkgconfig(Qt5Gui)
BuildRequires:	pkgconfig(Qt5Widgets)
BuildRequires:	qt5-platformtheme-gtk2
BuildRequires:	rhash-devel
BuildRequires:	cmake(jsoncpp)
# Ensure tests of Qt5Gui's cmake builds don't result in an error
# because libqdirectfb.so and friends have been "removed" since creating the
# cmake module
BuildRequires:	%{mklibname qt5gui 5}-offscreen
BuildRequires:	%{mklibname qt5gui 5}-x11
BuildRequires:	%{mklibname qt5gui 5}-linuxfb
BuildRequires:	%{mklibname qt5gui 5}-minimal
%endif
BuildRequires:	rhash-devel
BuildRequires:	gcc-gfortran
# For compatibility with Fedora and Mageia
Provides:	cmake-filesystem = %{EVRD}
Provides:	cmake-filesystem%{?_isa} = %{EVRD}
%ifarch %{arm}
Provides:	cmake-filesystem(armel-32) = %{EVRD}
%endif

%description
CMake is used to control the software compilation process using
simple platform and compiler independent configuration files.
CMake generates native makefiles and workspaces that can be
used in the compiler environment of your choice. CMake is quite
sophisticated: it is possible to support complex environments
requiring system configuration, pre-processor generation, code
generation, and template instantiation.

%files
%{_bindir}/cmake
%{_bindir}/ccmake
%{_bindir}/ctest
%{_bindir}/cpack
%{_datadir}/%{name}
%{_sysconfdir}/emacs/site-start.d/%{name}.el
%{_rpmmacrodir}/macros.cmake
%{_rpmconfigdir}/fileattrs/%{name}.attr
%{_rpmconfigdir}/%{name}.*
%{_datadir}/emacs/site-lisp/cmake-mode.el
%{_datadir}/vim/*/*
%{_datadir}/aclocal/cmake.m4

%package doc
Summary:	Documentation for %{name}
Group:		Development/Other
BuildArch:	noarch
Conflicts:	%{name} < 3.5.2-3

%description doc
Documentation for %{name}.

%files doc
%doc CMakeLogo.gif mydocs/*

#-----------------------------------------------------------------------------

%if !%{with bootstrap}
%package -n	%{name}-qtgui
Summary:	Qt GUI Dialog for CMake - the Cross-platform, open-source make system
Group:		Development/Other
Requires:	%{name}
# (tpg) Fix for bug https://issues.openmandriva.org/show_bug.cgi?id=833
Requires:	%{_lib}qt5gui5
Requires:	%{_lib}xcb-util-renderutil0
Requires:	%{_lib}xcb-icccm4

%description -n	%{name}-qtgui
CMake is used to control the software compilation process using
simple platform and compiler independent configuration files.

This is the Qt GUI.

%files -n %{name}-qtgui
%{_bindir}/cmake-gui
%{_datadir}/applications/cmake-gui.desktop
%{_datadir}/mime/packages/cmakecache.xml
%{_datadir}/icons/*/*/*/CMakeSetup.png
%endif

#-----------------------------------------------------------------------------

%prep
%if "%{beta}" != ""
%setup -qn %{name}-%{version}-%{beta}
%else
%setup -q
%endif
%apply_patches

# Don't try to automagically find files in /usr/X11R6
# But also don't change a prefix if it is not /usr
perl -pi -e 's@^\s+/usr/X11R6/.*\n@@' Modules/*.cmake

%ifarch %{arm}
# bootstrap test is taking ages on arm
sed -i -e 's!SET(CMAKE_LONG_TEST_TIMEOUT 1500)!SET(CMAKE_LONG_TEST_TIMEOUT 7200)!g' Tests/CMakeLists.txt
%endif

%build

mkdir -p build
cd build
%setup_compile_flags
../configure \
    --system-libs \
    --prefix=%{_prefix} \
    --datadir=/share/%{name} \
    --mandir=/share/man \
    --docdir=/share/doc/%{name} \
%if !%{with bootstrap}
    --qt-gui \
    --qt-qmake=%{_bindir}/qmake-qt5 \
%else
    --no-system-jsoncpp \
    --no-system-librhash \
%endif
    --parallel=%{_smp_mflags}

%make

%install
%makeinstall_std -C build

# vim syntax highlighting and indentation rules...
mv %{buildroot}%{_datadir}/cmake/editors/vim %{buildroot}%{_datadir}

# cmake mode for emacs
mkdir -p %{buildroot}%{_datadir}/emacs/site-lisp %{buildroot}%{_sysconfdir}/emacs/site-start.d
mv %{buildroot}%{_datadir}/cmake/editors/emacs/cmake-mode.el %{buildroot}%{_datadir}/emacs/site-lisp/cmake-mode.el
cat <<EOF >%{buildroot}%{_sysconfdir}/emacs/site-start.d/%{name}.el
(setq load-path (cons (expand-file-name "/dir/with/cmake-mode") load-path))
(require 'cmake-mode)
(setq auto-mode-alist
      (append '(("CMakeLists\\\\.txt\\\\'" . cmake-mode)
                ("\\\\.cmake\\\\'" . cmake-mode))
              auto-mode-alist))
EOF

# remove directory we just cleared by moving files where editors
# will actually find them
rm -rf %{buildroot}%{_datadir}/cmake/editors

# RPM macros and dependency generators
install -m644 %{S:1} -D %{buildroot}%{_rpmmacrodir}/macros.cmake
install -m644 %{S:2} -D %{buildroot}%{_rpmconfigdir}/fileattrs/%{name}.attr
install -m755 %{S:3} -D %{buildroot}%{_rpmconfigdir}/%{name}.prov
install -m755 %{S:4} -D %{buildroot}%{_rpmconfigdir}/%{name}.req

# %doc wipes out files in doc dir, fixed in cooker svn for rpm package, though
# not submitted yet, so we'll just work around this by moving it for now..
rm -rf mydocs
mv %{buildroot}%{_datadir}/doc/%{name} mydocs

# FIXME FIXME FIXME FIXME
# Workaround for libdnf bug
# https://github.com/rpm-software-management/libdnf/pull/543
# Need to work around it here because libdnf requires cmake to build...
# Get rid of this workaround as soon as fixed dnf is deployed in abf.
rm -rf %{buildroot}%{_datadir}/cmake/Help/generator/*' '*

# As of 2.8.10.2, the test suite needs net access.
# Absent that, it will fail:
# The following tests FAILED:
#        186 - CTestTestFailedSubmit-http (Failed)
#        187 - CTestTestFailedSubmit-https (Failed)
%if 0
%check
unset DISPLAY
cd build
bin/ctest -E SubDirSpaces -V %{_smp_mflags}
%endif
