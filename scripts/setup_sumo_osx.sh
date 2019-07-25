#!/bin/bash
echo "Installing system dependencies for SUMO"
# rllab dependencies
brew install swig sdl sdl_image sdl_mixer sdl_ttf portmidi
# sumo dependencies
brew install Caskroom/cask/xquartz autoconf automake pkg-config libtool gdal proj xerces-c fox

echo "Installing sumo binaries and python tools"
mkdir -p $HOME/sumo_binaries
pushd $HOME/sumo_binaries
git clone https://github.com/eclipse/sumo.git
cd sumo
git checkout 2147d155b1
cmake .
make -j$(nproc)
popd

export PATH="$PATH:$HOME/sumo_binaries/sumo/bin" >> ~/.bashrc
export SUMO_HOME="$HOME/sumo_binaries/sumo" >> ~/.bashrc
export PYTHONPATH="$PYTHONPATH:$HOME/sumo_binaries/sumo/tools" >> ~/.bashrc

echo 'Add the following to your ~/.bashrc:'
echo ''
echo 'export PATH="$PATH:$HOME/sumo_binaries/sumo/bin" >> ~/.bashrc'
echo 'export SUMO_HOME="$HOME/sumo_binaries/sumo" >> ~/.bashrc'
echo 'export PYTHONPATH="$PYTHONPATH:$HOME/sumo_binaries/sumo/tools" >> ~/.bashrc'
