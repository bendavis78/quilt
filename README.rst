quilt
=====

Quilt is a framework for modular add-ons using fabric. Quilt also provides an 
API for configuration management called "resources".  While Quilt Resources are
inspired by more robust CM systems such as Puppet or Chef, they are not 
intended to be a replacement for those systems. Resources are designed with
individual deployments in mind.  That is, it gives you a system to handle your 
vhosts, work process configs, directory layouts, etc.  Resources are defined as
instantiated python classes right within in your fabfile.  A simple call to 
"ensure" on that resource will ensure that resource's state.

Quilt is built on fabric, so it is all "push" and no "pull". That is, instead 
of a central server that nodes pull configs from, you are applying your 
configuration using a fabric command.
