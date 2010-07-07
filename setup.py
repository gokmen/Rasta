#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Rasta RST Editor
    2010 - Gökmen Göksel <gokmen:pardus.org.tr> '''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

# Python Libs
import os
import sys
import glob
import shutil

# DistUtils
from distutils.core import setup
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.command.install import install
from distutils.sysconfig import get_python_lib

# RastaLibs
from rasta_lib import __version__

PROJECT = 'rasta'
PROJECT_LIB = 'rasta_lib'

def update_messages():
    os.system('rm -rf .tmp')
    os.makedirs('.tmp')
    os.system('pyuic4 gui/mainWindow.ui -o %s/mainWindow.py -g %s' %
             (PROJECT_LIB, PROJECT))
    os.system('cp -R %s/*.py .tmp/' % PROJECT_LIB)
    os.system('cp rasta .tmp/rasta-app.py')
    os.system('ls .tmp/* | xargs xgettext --default-domain=%s '
              '--keyword=_ --keyword=i18n -o po/%s.pot' % (PROJECT, PROJECT))
    for item in os.listdir('po'):
        if item.endswith('.po'):
            os.system('msgmerge --no-wrap --sort-by-file -q -o .tmp/temp.po '
                      'po/%s po/%s.pot' % (item, PROJECT))
            os.system('cp .tmp/temp.po po/%s' % item)
    os.system('rm -rf .tmp')

class Clean(clean):
    def run(self):
        print 'Cleaning ...'
        os.system('find -name *.pyc|xargs rm -rf')
        for compiled in ('%s/mainWindow.py' % PROJECT_LIB,
                         '%s/icons_rc.py' % PROJECT_LIB):
            if os.path.exists(compiled):
                print ' removing: ', compiled
                os.unlink(compiled)
        for dirs in ('build', 'dist'):
            if os.path.exists(dirs):
                print ' removing: ', dirs
                shutil.rmtree(dirs)
        clean.run(self)

class Build(build):
    def run(self):
        print 'Building ...'
        os.system('pyuic4 gui/mainWindow.ui -o %s/mainWindow.py -g %s' %
             (PROJECT_LIB, PROJECT))
        os.system('pyrcc4 %s/icons.qrc -o %s/icons_rc.py' %
                 (PROJECT_LIB, PROJECT_LIB))
        build.run(self)

class Dist(sdist):
    def run(self):
        os.system('python setup.py build')
        sdist.run(self)

class Uninstall(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        print 'Uninstalling ...'
        project_dir = os.path.join(get_python_lib(), PROJECT_LIB)
        data_dir    = '/usr/share/%s' % PROJECT
        directories = (project_dir, data_dir)
        for directory in directories:
            if os.path.exists(directory):
                print ' removing: ', directory
                shutil.rmtree(directory)
        executable = '/usr/bin/%s' % PROJECT
        if os.path.exists(executable):
            print ' removing: ', executable
            os.unlink(executable)

class Install(install):
    def run(self):
        install.run(self)

        root_dir = '/usr/share'
        if self.root:
            root_dir = '%s/usr/share' % self.root

        locale_dir = os.path.join(root_dir, 'locale')
        # Install locales
        print 'Installing locales...'
        for filename in glob.glob1('po', '*.po'):
            lang = filename.rsplit('.', 1)[0]
            os.system('msgfmt po/%s.po -o po/%s.mo' % (lang, lang))
            try:
                os.makedirs(os.path.join(locale_dir, '%s/LC_MESSAGES' % lang))
            except OSError:
                pass
            shutil.copy('po/%s.mo' % lang, os.path.join(locale_dir,
                 '%s/LC_MESSAGES' % lang, '%s.mo' % PROJECT))

if 'update_messages' in sys.argv:
    update_messages()
    sys.exit(0)

setup(name=PROJECT,
      version=__version__,
      description='Rasta: The Rst Editor',
      long_description='Live view supported Qt4 based Webkit integrated Rst editor for Pardus Developers and all others.',
      license='GNU GPL2',
      author='Gökmen Göksel',
      author_email='gokmen@pardus.org.tr',
      url='http://developer.pardus.org.tr',
      packages=[PROJECT_LIB],
      scripts=[PROJECT],
      data_files = [('/usr/share/%s' % PROJECT, ['AUTHORS', 'README', 'COPYING', 'HELP'])],
      cmdclass = {
          'uninstall':Uninstall,
          'install'  :Install,
          'build'    :Build,
          'clean'    :Clean,
          'sdist'    :Dist,
          }
     )
