#!/bin/bash

#
# Taken from https://gist.github.com/josephwecker/2884332
#
CURDIR="${BASH_SOURCE[0]}";RL="readlink";([[ `uname -s`=='Darwin' ]] || RL="$RL -f")
while([ -h "${CURDIR}" ]) do CURDIR=`$RL "${CURDIR}"`; done
N="/dev/null";pushd .>$N;cd `dirname ${CURDIR}`>$N;CURDIR=`pwd`;popd>$N

function symlink_py {
    ln -s `python -c 'import '${1}', os.path, sys; sys.stdout.write(os.path.dirname('${1}'.__file__))'` $CURDIR/zato_extra_paths
}

rm -rf $CURDIR/bin
rm -rf $CURDIR/develop-eggs
rm -rf $CURDIR/downloads
rm -rf $CURDIR/eggs
rm -rf $CURDIR/include
rm -rf $CURDIR/.installed.cfg
rm -rf $CURDIR/lib
rm -rf $CURDIR/parts
rm -rf $CURDIR/zato_extra_paths

# Always run an update so there are no surprises later on when it actually
# comes to fetching the packages from repositories.
sudo apt-get update

sudo apt-get install bzr gfortran haproxy  \
    ruby-sass libatlas-dev libatlas3gf-base libblas3gf \
    libevent-dev libgfortran3 liblapack-dev liblapack3gf \
    libpq-dev libyaml-dev libxml2-dev libxslt1-dev libumfpack5.4.0 \
    openssl python2.7-dev python-m2crypto python-numpy python-pip \
    python-scipy python-zdaemon swig uuid-dev uuid-runtime

mkdir $CURDIR/zato_extra_paths

symlink_py 'M2Crypto'
symlink_py 'numpy'
symlink_py 'scipy'

sudo pip install --upgrade distribute
sudo pip install --upgrade virtualenv

virtualenv .

$CURDIR/bin/python bootstrap.py -v 1.7.0
$CURDIR/bin/buildout

echo
echo OK
