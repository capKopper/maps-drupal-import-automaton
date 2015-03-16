#!/bin/bash

if [ "$(whoami)" == "root" ]; then
  apt-get update

  echo "Installing pip, virtualenv and virtualenvwrapper..."
  apt-get install python-pip -y
  pip install virtualenv
  pip install virtualenvwrapper

  echo "Setup virtualenv for maps-import ..."
  export WORKON_HOME=$(pwd)/.venvs
  mkdir -p $WORKON_HOME
  source /usr/local/bin/virtualenvwrapper.sh
  mkvirtualenv maps-import

  echo "Installing dependencies ..."
  apt-get install libyaml-dev python-dev -y
  pip install -r requirements.txt
else
  echo "You must be root to run this script"
  exit 1
fi
