%define shortVersion %(echo %{version} | cut -d. -f1,2)

%bcond_with bootstrap

# Keep this in sync with the list of cross tools we build
# in other packages (binutils, gcc, ...)
%global targets aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv32-linuxmusl riscv64-linuxmusl aarch64-linuxuclibc armv7hnl-linuxuclibc i686-linuxuclibc x86_64-linuxuclibc x32-linuxuclibc riscv32-linuxuclibc riscv64-linuxuclibc aarch64-android armv7l-android armv8l-android x86_64-android i686-mingw32 x86_64-mingw32 ppc64le-linux ppc64le-linuxmusl ppc64le-linuxuclibc ppc64-linux ppc64-linuxmusl ppc64-linuxuclibc
%global long_targets %(
	for i in %{targets}; do
		CPU=$(echo $i |cut -d- -f1)
		OS=$(echo $i |cut -d- -f2)
		echo -n "$(rpm --target=${CPU}-${OS} -E %%{_target_platform}) "
	done
)

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

#define beta rc5

%ifarch %{arm}
# https://gitlab.kitware.com/cmake/cmake/-/issues/20568
%global optflags %{optflags} -D_FILE_OFFSET_BITS=64
%endif
%ifarch %{aarch64}
# On builders with a lot of cores but not a lot of memory,
# cmake builds tend to get killed by the OOM killer
%global optflags %{optflags} -g1
%endif

Name:		cmake
Summary:	Cross-platform, open-source make system
Version:	3.30.5
Release:	2
Source0:	http://www.cmake.org/files/v%{shortVersion}/%{name}-%{version}%{?beta:-%{beta}}.tar.gz
License:	BSD
Group:		Development/Other
Url:		https://www.cmake.org/HTML/index.html
Source1:	cmake.macros
Source2:	https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.attr
# cmake.prov is based on Fedora's versions found at
# https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.prov
# And fixed up to handle e.g. cmake(PkgConfig) correctly.
Source3:	cmake.prov
# cmake.req is based on Fedora's versions found at
# https://src.fedoraproject.org/rpms/cmake/raw/master/f/cmake.req
# And extended with a simplistic check for KDE Frameworks interdependencies
# Also, we drop the cmake-filesystem requirement (which is a non-issue in OM)
Source4:	cmake.req
Source100:	cmake.rpmlintrc
Patch0:		cmake-3.23.2-qt6-searchpath.patch
# cmake export files include an "integrity check" to make sure all related
# files are installed -- but it frequently does more harm than good, e.g.
# insisting all LLVM static libraries are installed when only the shared
# library is being used, or making sure all Qt style plugins are installed
# when QtGui is being used without needing any styles.
# Turn the fatal error into a warning.
Patch1:		cmake-3.24.0-dont-barf-on-integrity-check.patch
# Similar check for a missing directory referenced as include path
Patch2:		cmake-3.30.4-dont-barf-on-missing-directory.patch
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
BuildRequires:	cmake(cppdap)
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
%{_rpmmacrodir}/macros.buildsys.cmake
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
%doc CMakeLogo.gif
%if ! %{cross_compiling}
%doc mydocs/*
%endif

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

# Find Qt 6 (cont. from Patch0)
sed -i -e 's,@QT6DIR@,%{_libdir}/qt6,g' Source/cmFindCommon.cxx

%ifarch %{arm}
# bootstrap test is taking ages on arm
sed -i -e 's!SET(CMAKE_LONG_TEST_TIMEOUT 1500)!SET(CMAKE_LONG_TEST_TIMEOUT 7200)!g' Tests/CMakeLists.txt
%endif

%if %{cross_compiling}
%cmake \
	-DCMAKE_DATA_DIR=share/cmake \
	-DCMAKE_MAN_DIR=share/man \
	-DCMAKE_DOC_DIR=share/doc/cmake
%else
mkdir -p build
cd build
%set_build_flags
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
%endif

%build
%make_build -C build

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

# Create toolchain files for supported and semi-supported
# crosscompilers...
mkdir -p %{buildroot}%{_datadir}/cmake/toolchains
for i in %{long_targets}; do
	SV=1
	if echo $i |grep -qi linux; then
		SYSTEM=Linux
	elif echo $i |grep -qi android; then
		SYSTEM=Android
	elif echo $i |grep -qi mingw; then
		SYSTEM=Windows
		SV=10.0
	else
		SYSTEM=$(echo ${i}|cut -d- -f3)
	fi
	ARCH=$(echo ${i}|cut -d- -f1)
	case $ARCH in
	arm*)
		ARCH=arm
		;;
	i?86|pentium?|athlon)
		ARCH=i386
		;;
	znver*|x86_64*)
		ARCH=x86_64
		;;
	esac

	cat >%{buildroot}%{_datadir}/cmake/toolchains/${i}.toolchain <<EOF
set(CMAKE_SYSTEM_NAME $SYSTEM)
set(CMAKE_SYSTEM_VERSION $SV)
set(CMAKE_SYSTEM_PROCESSOR $ARCH)

set(CMAKE_SYSROOT %{_prefix}/$i)

set(CMAKE_C_COMPILER %{_bindir}/clang)
set(CMAKE_C_COMPILER_TARGET $i)
set(CMAKE_CXX_COMPILER %{_bindir}/clang++)
set(CMAKE_CXX_COMPILER_TARGET $i)

set(CMAKE_FIND_ROOT_PATH %{_prefix}/$i)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM BOTH)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
EOF
	cat >%{buildroot}%{_datadir}/cmake/toolchains/${i}-gcc.toolchain <<EOF
set(CMAKE_SYSTEM_NAME $SYSTEM)
set(CMAKE_SYSTEM_VERSION 1)
set(CMAKE_SYSTEM_PROCESSOR $ARCH)

set(CMAKE_SYSROOT %{_prefix}/$i)

set(CMAKE_C_COMPILER %{_bindir}/$i-gcc)
set(CMAKE_CXX_COMPILER %{_bindir}/$i-g++)

set(CMAKE_FIND_ROOT_PATH %{_prefix}/$i)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM BOTH)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
EOF
done

# RPM macros and dependency generators
install -m644 %{S:1} -D %{buildroot}%{_rpmmacrodir}/macros.buildsys.cmake
install -m644 %{S:2} -D %{buildroot}%{_rpmconfigdir}/fileattrs/%{name}.attr
install -m755 %{S:3} -D %{buildroot}%{_rpmconfigdir}/%{name}.prov
install -m755 %{S:4} -D %{buildroot}%{_rpmconfigdir}/%{name}.req

# %doc wipes out files in doc dir, fixed in cooker svn for rpm package, though
# not submitted yet, so we'll just work around this by moving it for now..
%if ! %{cross_compiling}
rm -rf mydocs
mv %{buildroot}%{_datadir}/doc/%{name} mydocs
%else
rm -rf %{buildroot}%{_datadir}/doc/%{name}
%endif

# As of 3.26.4, the following are known to FAIL:
#        132 - CPackComponentsForAll-RPM-default (Failed)
#        133 - CPackComponentsForAll-RPM-OnePackPerGroup (Failed)
#        134 - CPackComponentsForAll-RPM-IgnoreGroup (Failed)
#        135 - CPackComponentsForAll-RPM-AllInOne (Failed)
#        428 - RunCMake.ParseImplicitLinkInfo (Failed)
#        486 - RunCMake.find_package (Failed)
#        583 - RunCMake.CPack_RPM.CUSTOM_NAMES (Failed)
#        584 - RunCMake.CPack_RPM.DEBUGINFO (Failed)
#        588 - RunCMake.CPack_RPM.EMPTY_DIR (Failed)
#        590 - RunCMake.CPack_RPM.INSTALL_SCRIPTS (Failed)
#        591 - RunCMake.CPack_RPM.MAIN_COMPONENT (Failed)
#        594 - RunCMake.CPack_RPM.PER_COMPONENT_FIELDS (Failed)
#        595 - RunCMake.CPack_RPM.SINGLE_DEBUGINFO (Failed)
#        596 - RunCMake.CPack_RPM.EXTRA_SLASH_IN_PATH (Failed)
%if 0
%check
unset DISPLAY
cd build
bin/ctest -E SubDirSpaces -V %{_smp_mflags}
%endif
