About
======

**Scriptim -- scriptor improved**

is a python clone of scriptor, a console to interact with smartcard readers.

latest version and additionnal info can be found at:
http://github.com/bernardpaulus/scriptim

::

  #    Copyright 2011 Bernard Paulus <bprecyclebin@gmail.com>
  #
  #    This file is part of scriptim
  #
  #    scriptim is free software: you can redistribute it and/or modify
  #    it under the terms of the GNU General Public License as published by
  #    the Free Software Foundation, either version 3 of the License, or
  #    (at your option) any later version.
  #
  #    This program is distributed in the hope that it will be useful,
  #    but WITHOUT ANY WARRANTY; without even the implied warranty of
  #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  #    GNU General Public License for more details.
  #
  #    You should have received a copy of the GNU General Public License
  #    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Features
=========

Scriptim supports:
 * readline command-line edition capabilities:
   in-place command edition, bash-like history (~/.scriptim_history file)
 * automatic detection and display of ascii data, with an error probability of
   less than 1%.
 * shortcuts for hexadecimal commands
 * error detection in return values

Scriptim does not support yet:
 * extensive return value interpretation
 * manual protocol selection

Scriptim additionnally targets to:
 * support automated authentication

Install
========

to run scriptim, you'll need:
python (works at least under 2.6 and 2.7), pcsc_lite, pyscard and ccid

Mac OS/X snow leopard
----------------------

 * Go to the touchatag website, create an account there, download & extract the
   archive for mac
   http://www.touchatag.com/downloads

 * You'll have driver.dmg, install and restart computer
 * install touchatag.dmg, also present. Launch app, and wait for it's connection
   to the server.
 * Install pyscard from http://sourceforge.net/projects/pyscard/
 * Download scriptim https://github.com/bernardpaulus/scriptim

debian
-------

You can obtain the required programs on debian by typing this:
sudo aptitude install pcsc-tools python-pyscard libccid

the latest version of scriptim can be found at
https://github.com/bernardpaulus/scriptim

Running
========

Just type ./scriptim.py or python scriptim.py
use option -h or --help for help about running

Commands within scriptim
-------------------------

There are two kinds of commands:

 * normal commands : commands that will be sent to the card reader
 * scriptim control commands: commands used to change the current card reader, exit, ...

Commands can include "#" comments and backslash-continuation of commands

Normal commands
~~~~~~~~~~~~~~~~

Canonical normal commands are composed of bytes in hexadecimal notation. That is
groups of 2 hexadecimal characters.

    Example::

        FF 00 48 00 00 , FF 00 40 50 04 05 05 03 01

Scriptim, however, admits some shortcuts:

 * you may write groups that begin by '0' only by writing their low-order hex
   Example::

       FF 0 48 0 0
       FF 0 40 50 4 5 5 3 1

 * you may collate any number of groups together, on the condition that they are
   not shortcuts of a high-order '0', like above
   Example::

       FF00 480000
       FF0040500405050301

scriptim control commands
~~~~~~~~~~~~~~~~~~~~~~~~~~

scriptim currently admits 2 types of commands:

 * exit commands: exit, quit, EOF (<CTRL+D>)
   those commands cause scriptim to exit immediately, regardless of being part
   of a backslash-continued command

 * connection commands: reset, changereader
   both cause the connection to be renewed. changereader allows the selection
   of a different reader, or even no reader

comments, and backslash-continued commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comments are marked by '#'. That mark, and everything that follows will be
ignored

Backslash-continued commands. If a backslash '\' is the last character on that
line, excluding comments, the next command is the continuation of the current
command, last backslash removed.

Example::

    FF 00 48\# beginning of the command
    00 00    # end of the command

is equivalent to::

    FF 00 48 00 00


Known problems
===============

On debian, sometimes pcsc will cause syslog to print a small message.
tail /var/log/syslog

shows messages like:

pcscd: pcscdaemon.c:663:clean_temp_files() Cannot remove ...

This is due to a bug of pcsc_lite that has been fixed in the svn, but not yet
packaged.

http://archives.neohapsis.com/archives/dev/muscle/current/0040.html
(EDIT: the page doesn't seem accessible the 2 of october 2011)
