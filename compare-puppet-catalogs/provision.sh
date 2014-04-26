#!/bin/bash
RUBYVER="1.8.7"
apt-get update
apt-get -y install curl git-core vim python-pip python-dev
# Install rvm (I know, this is horrible, curling and executing in a shell should be prohibited)
if [ ! -f /usr/local/rvm/scripts/rvm ]; then
   curl -sSL https://get.rvm.io | bash -s stable --ruby
   gpasswd -a vagrant rvm
fi;

. /usr/local/rvm/scripts/rvm

#This is already idempotent, no need for checks here
rvm install ${RUBYVER}
rvm use ${RUBYVER}



gem list | fgrep bundler > /dev/null

if [ $? -ne 0 ]; then
    gem install bundler
fi;

for puppet in 2.7 3; do
    /vagrant/shell/installer ${puppet} ${RUBYVER}
done

# Install puppet catalog diff Face
pushd /vagrant/shell
sudo -u vagrant mkdir -p /home/vagrant/.puppet/modules
sudo -u vagrant /usr/local/rvm/bin/rvm ${RUBYVER} do bundle exec puppet module install ripienaar-catalog_diff
popd

sudo pip install simplediff
sudo pip install jinja2

for dir in compiled diff html; do
    sudo -u vagrant mkdir -p /vagrant/output/${dir}
done

echo "Now you just need to:"
echo " - create an archive with facts named puppet-facts.xz from a puppet master"
echo "   and copy it here"
echo " - run the './shell/helper install' script"
