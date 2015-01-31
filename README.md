ACC CLIENT
===========

The Amaret Cloud Compiler Client: pollenc

#INSTALL

`sudo pip install git+https://YOUR_USER_ID@bitbucket.org/amaret/acc.client.git`

The above command will install pollenc in your system path, usually in `/usr/local/bin`

#UN-INSTALL

`sudo pip uninstall pollenc`


#NOTES

The above commands work with private git repos and require git to be installed
locally and that the user have an account at bitbucket.org.

To ease distribution on release date, we should create an public git repo and
remove the YOUR_USER_ID part of the above command.

_We may want to consider a private binary pypiserver instance to remove the
git requirement_

During development, to test the pollenc commmand from the system path and to
test the setup.py, install with `sudo pip install .`.

