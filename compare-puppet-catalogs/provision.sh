#!/bin/bash
RUBYVER="1.8.7"
apt-get update
apt-get -y install curl git-core vim python-pip python-dev
apt-get -y install ruby1.8 rubygems ruby-bundler libsqlite3-dev
echo mysql-server-5.5 mysql-server/root_password password cucciolo | debconf-set-selections
echo mysql-server-5.5 mysql-server/root_password_again password cucciolo | debconf-set-selections
apt-get install -y mysql-common mysql-server mysql-client
apt-get -y install ruby-mysql nginx

mysql -pcucciolo -NBe 'CREATE DATABASE puppet'
mysql -pcucciolo -NBe "GRANT ALL PRIVILEGES ON puppet.* TO 'puppet' IDENTIFIED BY 'puppet'"

for puppet in 2.7 3; do
    /vagrant/shell/installer ${puppet}
done

# Install puppet catalog diff Face, under puppet 3
pushd /vagrant/shell/env_puppet_3
test -f Gemfile.lock || bundle > /dev/null
bundle exec puppet module install ripienaar-catalog_diff
popd

pip install simplediff jinja2 requests

for dir in compiled diff html; do
    mkdir -p /vagrant/output/${dir}
done

# Show results in a browser.
cp /vagrant/nginx.vhost /etc/nginx/sites-available/default
# And this is horrible and hackish, but still...
perl -i"" -pe 's/^(\s*text\/plain\s*txt);$/$1 warnings pson;/' /etc/nginx/mime.types
/etc/init.d/nginx restart



echo "Now you just need to:"
echo " - create an archive with facts named puppet-facts.xz from a puppet master"
echo "   and copy it here"
echo " - run the './shell/helper install' script"
echo "SEE THE README FOR DETAILS"
