#!/bin/bash


cd build

python setup.py --command-packages=stdeb.command debianize

tar czvf ../nocsys-sonic-gnmi-server_0.1.orig.tar.gz .

cp postinst debian/python-nocsys-sonic-gnmi-server.postinst

dpkg-buildpackage
