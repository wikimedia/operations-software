swiftrepl
=========

swiftrepl performs one-way synchronization between two different swift
clusters. It is possible to restrict what will be synchronized by container
name and file name.

testing
-------
One easy way to test swiftrepl at a very high level is to spawn two local swift
clusters using SAIO and two vagrant virtual machines:

  git clone https://github.com/swiftstack/vagrant-swift-all-in-one.git vagrant-saio1
  git clone https://github.com/swiftstack/vagrant-swift-all-in-one.git vagrant-saio2

  (cd vagrant-saio1 && vagrant up)
  (cd vagrant-saio2 && export IP=192.168.8.81 && vagrant up)

If you are on Linux you might want to also `export SOURCE_ROOT=/tmp` since
vboxfs mounted at `/vagrant` doesn't like symlinks. A sample configuration file
`swiftrepl.conf.saio` is provided that can be used out of the box. The two
swift clusters can be inspected for example with `python-swiftclient` and
setting `ST_USER` `ST_KEY` `ST_AUTH` as indicated in the sample configuration.
