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

# Script for downloading third-party libraries for the realtime help XBlock.

# Force shell to fail on any errors.
set -e

LIBS_ROOT=chat/public/lib

STROPHE_JS_URL=https://cdnjs.cloudflare.com/ajax/libs/strophe.js/1.1.3/strophe.min.js
STROPHE_JS_DIRNAME=strophejs

CANDY_JS_GIT_URL=https://github.com/candy-chat/candy.git
CANDY_JS_REPO_NAME=candy
CANDY_JS_TAG=v1.6.0

verify_and_set_current_location() {
  if [ ! -f "setup_chat_xblock.sh" ]; then
    echo
    echo   ERROR: This script should be run from the folder that contains it.
    echo   Terminating...
    echo
    exit 1
  fi

  CURRENT_LOCATION=$(pwd)
}

install_strophe_js() {
  cd $LIBS_ROOT
  mkdir $STROPHE_JS_DIRNAME
  cd $STROPHE_JS_DIRNAME
  wget $STROPHE_JS_URL -O strophe.min.js
  cd ../../../../
}

install_candy_js() {
  cd $LIBS_ROOT
  git clone $CANDY_JS_GIT_URL
  cd $CANDY_JS_REPO_NAME
  git checkout $CANDY_JS_TAG

  # Replace candy.bundle.js with the modified version.
  git apply $CURRENT_LOCATION/resources/candy.bundle.patch

  cd ../../../../
}

install_chat_xblock_dependencies() {
  verify_and_set_current_location

  mkdir -p $LIBS_ROOT
  install_strophe_js
  install_candy_js

  echo
  echo   Installation of libraries for chat XBlock completed.
  echo
}

install_chat_xblock_dependencies
