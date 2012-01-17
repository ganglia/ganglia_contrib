#!/usr/bin/env bash

PREFIX=/usr/graph001

BUILD_CONCURRENCY=1




#-------------------------------------------------
set -e
DOWNLOADS=${PREFIX}/work/tarballs
BUILDS=${PREFIX}/work/builds
RECEIPTS=${PREFIX}/.installed

# 3 variables inspired by Mozilla's crazy build system
# OS_ARCH e.g.Linux, SunOS, Darwin
# OS_CPUARCH, e.g. i86pc (solaris), x86, x86_64 (linux), i386 (darwin)
# OS_RELEASE, e.g. 2.6.21-2952xen (linux variant), 5.11 (solaris variant)

OS_ARCH=`uname -s`
OS_CPUARCH=`uname -m`
OS_RELEASE=`uname -r`

#
# Location of basic files... most of the time this won't need to be changed
#
TAR=tar
MAKE=make
BZCAT=bzcat
GZCAT="gunzip -c"
# some systems don't have sudo and run as root
SUDO=sudo
# something to download files, or curl or wget works
#WGET="curl -A Mozilla -O"
WGET=wget

# required by 'binutils' -- part of the gnu 'texinfo' package
MAKEINFO=makeinfo

export PATH=${PREFIX}/bin:${PATH}
export LDFLAGS="-L${PREFIX}/lib"
export CPPFLAGS=-I${PREFIX}/include
export CONFIG_SHELL=/bin/bash
export LD_LIBRARY_PATH=${PREFIX}/lib:${LD_LIBRARY_PATH}
if [ "${OS_ARCH}" = "Darwin" ]; then
 export DYLD_LIBRARY_PATH=$LD_LIBRARY_PATH
fi


function init_directories() {
    if [ ! -d $BUILDS ]; then
	mkdir -p ${BUILDS}
    fi

    if [ ! -d $PREFIX ]; then
	${SUDO} mkdir -p ${PREFIX}
    fi

    if [ ! -d $RECEIPTS ]; then
	${SUDO} mkdir -p ${RECEIPTS}
    fi

    if [ ! -d $DOWNLOADS ]; then
	${SUDO} mkdir -p ${DOWNLOADS}
    fi
}

function find_receipt()
{
    TARFILE=$1
    RECEIPT="${RECEIPTS}/${TARFILE}"
    if [ -f "${RECEIPT}" ]; then
	echo "Found receipt for ${TARFILE}";
        export HAS_RECEIPT=1;
    else
        export HAS_RECEIPT=0;
    fi
    return 0;
}

function write_receipt()
{
    RECEIPT="${RECEIPTS}/${TARFILE}"
    ${SUDO} touch ${RECEIPT}
}

function unpacktar()
{
    # given FULLFILE=/Downloads/gmp-4.2.4.tar.gz, then...
    # TARFILE = gmp.4.2.4.tar.gz
    # SUFFIX = 'gz'
    # TARDIR = gmp-4.2.4

    TARFILE="$1"
    TARDIR="$2"
    FULLFILE="${DOWNLOADS}/${TARFILE}";
    SUFFIX=${TARFILE/*./}
    if [ -z "${TARDIR}" ]; then
	TARDIR=${TARFILE/%.${SUFFIX}/}
	TARDIR=${TARDIR/%.tar/}
    fi
 
    UNPACK=""
    case ${SUFFIX} in
	('bz2')         { UNPACK="$BZCAT $FULLFILE"; } ;;
	('gz' | 'tgz')  { UNPACK="$GZCAT $FULLFILE"; } ;;
	('tar')         { UNPACK="cat $FULLFILE"; } ;;
    esac
    echo "UNPACK=${UNPACK}"
    # if not match, then exit
    if [ -z "${UNPACK}" ]; then
	echo "unknown tar file type: $SUFFIX for $FULLFILE";
	exit 1
    fi
    pushd .

    cd ${BUILDS}
    CMD="${UNPACK} | ${TAR} -xf -"
    echo "$CMD"
    eval $CMD

    cd $TARDIR
    CMD="${UNPACK} | tar -xf -"
}


function download_file()
{
    URL="$1"
    TARFILE="`basename $URL`"
    # get tarball
    if [ ! -f "${DOWNLOADS}/${TARFILE}" ]; then
	echo "Downloading ${URL}"
	(cd ${DOWNLOADS} && ${WGET} ${URL})
    fi
}

function installgnu()
{
    URL="$1"
    TARFILE="`basename $URL`"

    # $2 is 'configure args'
    CARGV="$2"

    # $3 is configure env, list as "KEY=VAL KEY2=VAL2...."
    CENV="$3"

    # sometimes, the directory created by untar is "non-standard"
    ALTDIR="$4"

    find_receipt $TARFILE
    if [ $HAS_RECEIPT -eq 1 ]; then
	return
    fi

    download_file $URL
    unpacktar $TARFILE $ALTDIR;

    #if [ ! -d objdir ]; then mkdir objdir; fi
    #cd objdir

    # the ${CARGV[@]} -- if string, then use it
    #   if array, do a 'join' on the argument, with ' ' as separator
    CMD="${CENV} ./configure --prefix=${PREFIX} ${CARGV[@]}"
    echo $CMD
    eval $CMD

    ${MAKE} -j ${BUILD_CONCURRENCY}
    ${SUDO} ${MAKE} install
    write_receipt $TARFILE
    popd
}

function install_python() {
    URL="$1"
    TARFILE="`basename $URL`"
    # $2 is 'configure args'
    CARGV="$2"

    find_receipt $TARFILE
    if [ $HAS_RECEIPT -eq 1 ]; then
	return
    fi
    download_file ${URL}
    unpacktar ${TARFILE}
    ${SUDO} python setup.py build ${CARGV}
    ${SUDO} python setup.py install 
    write_receipt ${TARFILE}
    popd
}

#-------------------------------------------------
init_directories

installgnu http://pkgconfig.freedesktop.org/releases/pkg-config-0.23.tar.gz
export PKG_CONFIG=${PREFIX}/bin/pkg-config

installgnu http://www.python.org/ftp/python/2.6.1/Python-2.6.1.tar.bz2 '--disable-toolbox-glue'
installgnu ftp://ftp.simplesystems.org/pub/libpng/png/src/libpng-1.2.34.tar.bz2

installgnu http://savannah.inetbridge.net/freetype/freetype-2.3.8.tar.bz2

installgnu ftp://xmlsoft.org/libxml2/libxml2-2.7.3.tar.gz
installgnu ftp://xmlsoft.org/libxml2/libxslt-1.1.24.tar.gz

installgnu http://fontconfig.org/release/fontconfig-2.6.0.tar.gz '--enable-libxml2 --disable-docs'

installgnu http://www.cairographics.org/releases/pixman-0.13.2.tar.gz
installgnu http://ftp.gnome.org/pub/gnome/sources/glib/2.18/glib-2.18.4.tar.bz2

#installgnu http://cairographics.org/releases/cairo-1.8.6.tar.gz


installgnu http://ftp.gnome.org/pub/GNOME/sources/pango/1.23/pango-1.23.0.tar.bz2

installgnu ftp://ftp.ruby-lang.org/pub/ruby/1.8/ruby-1.8.7-p72.tar.gz

installgnu http://oss.oetiker.ch/rrdtool/pub/rrdtool-1.3.6.tar.gz

install_python http://www.cython.org/Cython-0.10.3.tar.gz
install_python http://codespeak.net/lxml/lxml-2.1.5.tgz --with-xslt-config=${PREFIX}/bin/xslt-config

