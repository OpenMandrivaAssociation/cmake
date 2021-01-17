%define shortVersion %(echo %{version} | cut -d. -f1,2)

%bcond_with bootstrap

%if %{with bootstrap}
%bcond_with gui
%else
# The RISC-V port doesn't have Qt yet
%ifarch %{riscv}
%bcond_with gui
%else
%bcond_without gui
%endif
%endif

#define beta %{nil}

%ifarch %{arm}
# https://gitlab.kitware.com/cmake/cmake/-/issues/20568
%global optflags %{optflags} -D_FILE_OFFSET_BITS=64
%endif

Name:		cmake
Summary:	Cross-platform, open-source make system
Version:	3.19.3
Release:	1
Source0:	http://www.cmake.org/files/v%{shortVersion}/%{name}-%{version}%{?beta:-%{beta}}.tar.gz
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
Patch3:		cmake-3.4.1-dont-override-fPIC-with-fPIE.patch
BuildRequires:	perl
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libcurl)
BuildRequires:	pkgconfig(libidn)
BuildRequires:	pkgconfig(libuv)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	xz
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(bzip2)
BuildRequires:	pkgconfig(libarchive)
%if !%{with bootstrap}
# We need a copy of ourselves for the cmake(*) dependency generator to work
# and create all the cmake(*) Provides for the built-in modules
BuildRequires:	pkgconfig(libzstd)
BuildRequires:	cmake
BuildRequires:	cmake(jsoncpp)
%endif
%if %{with gui}
BuildRequires:	qmake5
BuildRequires:	pkgconfig(Qt5Gui)
BuildRequires:	pkgconfig(Qt5Widgets)
BuildRequires:	qt5-platformtheme-gtk2
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
%{_datadir}/bash-completion/completions/*

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

%if %{with gui}
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
%autosetup -n %{name}-%{version}%{?beta:-%{beta}} -p1

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
if ! ../configure \
    --system-libs \
    --prefix=%{_prefix} \
    --datadir=/share/%{name} \
    --mandir=/share/man \
    --docdir=/share/doc/%{name} \
%if %{with gui}
    --qt-gui \
    --qt-qmake=%{_bindir}/qmake-qt5 \
%endif
%if %{with bootstrap}
    --no-system-jsoncpp \
    --no-system-librhash \
%endif
    --parallel=%{_smp_mflags}; then
	cat Bootstrap.cmk/cmake_bootstrap.log
	exit 1
fi

%make_build

%install
%make_install -C build

# cmake mode for emacs
mkdir -p %{buildroot}%{_sysconfdir}/emacs/site-start.d
cat <<EOF >%{buildroot}%{_sysconfdir}/emacs/site-start.d/%{name}.el
(setq load-path (cons (expand-file-name "/dir/with/cmake-mode") load-path))
(require 'cmake-mode)
(setq auto-mode-alist
      (append '(("CMakeLists\\\\.txt\\\\'" . cmake-mode)
                ("\\\\.cmake\\\\'" . cmake-mode))
              auto-mode-alist))
EOF

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
