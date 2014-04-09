#!/usr/bin/env bash

# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# author: sll@google.com (Sean Lip)
#
# Script for setting up the ejabberd chat server on a virtual machine.
#
# More information on running ejabberd can be found here:
#
#     http://www.process-one.net/docs/ejabberd/guide_en.html
#
# IMPORTANT: If you have installed ejabberd in the past, then do the following
# before running this script:
# - Terminate all existing ejabberd processes (e.g. using
#       'ps aux | grep ejabberd' and the 'kill' command)
# - Delete /etc/ejabberd/ejabberd.cfg


# Force shell to fail on any errors.
set -e

# This can be modified. It is where the ejabberd library files will be
# downloaded to.
INSTALLATION_ROOT=~/ejabberd_libs

EJABBERD_GIT_URL=https://github.com/processone/ejabberd
EJABBERD_REPO_NAME=ejabberd
EJABBERD_BRANCH=2.1.x
EJABBERD_COMMIT=a94dbbf1f892239068813bb6aeba50b7a6de4898

EJABBERD_CONTRIB_GIT_URL=https://github.com/processone/ejabberd-contrib.git
EJABBERD_CONTRIB_REPO_NAME=ejabberd-contrib
EJABBERD_CONTRIB_BRANCH=2.1.x
EJABBERD_CONTRIB_COMMIT=93bba1d1fd246499434190fc1ebcdbff28fb6fe6

verify_and_set_current_location() {
  if [ ! -f "setup_ejabberd.sh" ] || [ ! -d "resources" ]; then
    echo
    echo   ERROR: This script should be run from the folder that contains it
    echo   and a resources/ directory.
    echo   Terminating...
    echo
    exit 1
  fi

  CURRENT_LOCATION=$(pwd)
}

require_prerequisites() {
  sudo apt-get update
  sudo apt-get install git
  sudo apt-get install build-essential automake autoconf erlang erlang-manpages
  sudo apt-get install libexpat1-dev zlib1g-dev libssl-dev
}

checkout_ejabberd() {
  cd $INSTALLATION_ROOT
  git clone $EJABBERD_GIT_URL
  cd $EJABBERD_REPO_NAME
  git checkout -b $EJABBERD_BRANCH origin/$EJABBERD_BRANCH
  git checkout $EJABBERD_COMMIT
  cd $INSTALLATION_ROOT
}

checkout_ejabberd_contrib() {
  cd $INSTALLATION_ROOT
  git clone $EJABBERD_CONTRIB_GIT_URL
  cd $EJABBERD_CONTRIB_REPO_NAME
  git checkout -b $EJABBERD_CONTRIB_BRANCH origin/$EJABBERD_CONTRIB_BRANCH
  git checkout $EJABBERD_CONTRIB_COMMIT
  cd $INSTALLATION_ROOT
}

install_mod_rest() {
  cd $INSTALLATION_ROOT
  cd $EJABBERD_CONTRIB_REPO_NAME/mod_rest/
  ./build.sh
  cp ebin/mod_rest.beam $INSTALLATION_ROOT/$EJABBERD_REPO_NAME/src
  cd $INSTALLATION_ROOT
}

install_mod_admin_extra() {
  cd $INSTALLATION_ROOT
  cd $EJABBERD_CONTRIB_REPO_NAME/mod_admin_extra/
  ./build.sh
  cp ebin/mod_admin_extra.beam $INSTALLATION_ROOT/$EJABBERD_REPO_NAME/src
  cd $INSTALLATION_ROOT
}

install_mod_muc_admin() {
  cd $INSTALLATION_ROOT
  cd $EJABBERD_CONTRIB_REPO_NAME/mod_muc_admin/
  ./build.sh
  cp ebin/mod_muc_admin.beam $INSTALLATION_ROOT/$EJABBERD_REPO_NAME/src
  cd $INSTALLATION_ROOT
}

make_ejabberd() {
  cd $INSTALLATION_ROOT

  cd $EJABBERD_REPO_NAME/src
  ./configure
  make
  sudo make install

  cd $INSTALLATION_ROOT
}

verify_config_file() {
  cd $INSTALLATION_ROOT

  MD5_CHECKSUM=$(sudo md5sum /etc/ejabberd/ejabberd.cfg)
  EXPECTED_MD5_CHECKSUM='e96cb668e5e455eb49bb774418dc1304  /etc/ejabberd/ejabberd.cfg'
  if [ "$MD5_CHECKSUM" != "$EXPECTED_MD5_CHECKSUM" ]; then
    echo
    echo   ERROR: checksum of ejabberd.cfg file does not match expected value.
    echo   Terminating...
    echo
    exit 1
  fi

  cd $INSTALLATION_ROOT
}

modify_ejabberd_config() {
  cd $INSTALLATION_ROOT
  sudo cp /etc/ejabberd/ejabberd.cfg $INSTALLATION_ROOT/ejabberd.cfg
  sudo chmod 666 $INSTALLATION_ROOT/ejabberd.cfg

  git apply $CURRENT_LOCATION/resources/ejabberd_cfg.patch
  chmod 640 $INSTALLATION_ROOT/ejabberd.cfg
  sudo mv $INSTALLATION_ROOT/ejabberd.cfg /etc/ejabberd
  cd $INSTALLATION_ROOT
}

install_ejabberd() {
  verify_and_set_current_location

  require_prerequisites
  if [ -d $INSTALLATION_ROOT ]; then
    echo
    echo   ERROR: the installation directory must not already exist.
    echo   Terminating...
    echo
    exit 1
  fi
  mkdir -p $INSTALLATION_ROOT
  checkout_ejabberd
  checkout_ejabberd_contrib
  install_mod_rest
  install_mod_admin_extra
  install_mod_muc_admin
  make_ejabberd
  verify_config_file
  modify_ejabberd_config

  echo
  echo   Installation of ejabberd successfully completed.
  echo
  echo   To finish the process, open /etc/ejabberd/ejabberd.cfg in a text
  echo   editor, and search for the four @REALTIME_HELP_FIXME lines. Add the
  echo   IP addresses of the ejabberd and edX servers, as well as the path to
  echo   the SSH certificate file, following the directions in ejabberd.cfg.
  echo   This will allow both servers to communicate with the chat server.
  echo
}

install_ejabberd
