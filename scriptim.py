#!/usr/bin/python

#    scriptim - aka scriptor improved
#       python shell to interact with smartcards
#    
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


import sys
import re
import getopt, sys

import atexit # history stuff
import os

try: # improves current shell with command-line editing capabilities
    # TODO : support history between sessions
    import readline 
except ImportError:
    print "Module readline not available."
    print "Continuing with reduced functionnalities"

try:
    import smartcard

    # for error checking
    from smartcard.sw.ErrorCheckingChain import ErrorCheckingChain
    from smartcard.sw.ISO7816_4ErrorChecker import ISO7816_4ErrorChecker
    from smartcard.sw.ISO7816_8ErrorChecker import ISO7816_8ErrorChecker
    from smartcard.sw.ISO7816_9ErrorChecker import ISO7816_9ErrorChecker
    from smartcard.sw.SWExceptions import SWException, WarningProcessingException
except ImportError:
    print "No smartcard module found"
    print "on debian, try: sudo aptitude install python-pyscard"
    sys.exit(3)

def command_loop(fun_usrinput=lambda x: x not in ["quit", "exit", None] and
                              str(x) or None):
    """
    Reads user input then calls fun_usrinput(USER_INPUT) and prints the result (without carriage
return added) until fun_usrinput(USER_INPUT) returns None

NOTE: EOF is passed as None to fun_usrinput(). 

Default function only copies the input to stdout, except when feeded by quit,
exit, EOF (ctrl+D) or the empty string 
(because str("") evaluates to "" which is equivalent to False in a python
condition. This is a side-effect of the 'or')
"""

    ustr=None
    end_loop=False
    while end_loop is not True:
        # protected input
        try:
            ustr=raw_input()
        except EOFError:
            ustr=None

        # input treatment
        out=fun_usrinput(ustr)
        if out is None:
            end_loop=True
        elif len(str(out)) > 0:
            print (out)


def selector(choices_list, default_index=None):
    """Proposes a series of choices to the user and returns a couple 
(index of selected entry, entry)"""

    default_return=None
    if 0 <= default_index < len(choices_list): # default_index=None => False
        default_return=(default_index, choices_list[default_index])

    for i in xrange(len(choices_list)):
        if i == default_index:
            print "["+str(i)+"]\t", str(choices_list[i])
        else:
            print " "+str(i)+" \t", str(choices_list[i])

    try:
        choice=int(raw_input("Your number: ") or str(default_index))
        # in the case of empty or invalid entry, the default is returned
    except ValueError:
        if 0 <= default_index < len(choices_list):
            print "using default choice"
        else:
            print "invalid entry"
        return default_return

    if 0 <= choice < len(choices_list):
        return (choice, choices_list[choice])
    else:
        return default_return

def escape_backslashes(string):
    """escapes every backslash present in the string"""
    # you can use this to make a string become a re pattern for itself :)
    escape_if_backslash=lambda x: x == '\\' and "\\\\" or x
    return ''.join([escape_if_backslash(x) for x in string])
    
class fun_loop_creator:
    """this class provides a function which will treat the user input in the
loop: fun_usrinput

    The rest are helper functions
"""
    READER_NULL="No Reader" 
    # self.curreader == READER_NULL indicates that no actual reader is in use

    def __init__(self):
        self.curreader=None
        self.s=None
        self.reset()
        self.command_acc="" # empty unterminated command

        # error detection
        errorchain = []
        errorchain = [ErrorCheckingChain(errorchain, ISO7816_9ErrorChecker())]
        errorchain = [ErrorCheckingChain(errorchain, ISO7816_8ErrorChecker())]
        errorchain = [ErrorCheckingChain(errorchain, ISO7816_4ErrorChecker())]
        self.errorchain=errorchain

        # readline history
        histfile=os.path.expanduser('~/.scriptim_history')
        try:
            self.init_history(histfile)
        except NameError:
            pass


    def reset(self, reader=None):
        """scans for readers and renew the connection with the current reader,
if still present. If no connection could be established, self.s is None.

Calling this with no arguments, or None make this function attempt to renew the
connection with the previous reader, or ask the user for one either if there was
no previous reader or if it is not present anymore.

Calling it with a reader creates a new connection with
that reader, or ask the user for one if given reader is not present."""

        if self.s is not None: # already had a connection
            self.s.close()
            self.s=None

        # take given reader or previous reader
        curreader=reader or self.curreader 

        readers=smartcard.System.readers()
        if len(readers) == 0:
            print "no readers present. Smartcard commands are not sent."
            curreader=self.READER_NULL
        elif curreader is None or curreader not in smartcard.System.readers():
            if len(readers) == 1:
                curreader=readers[0]
                print "Using only present reader "+str(curreader)
            else:
                curreader=selector(readers, 0)[1]

        readers=[str(x) for x in smartcard.System.readers()]
        if (curreader is not None) and str(curreader) in readers:
            self.s=smartcard.Session(curreader)

        self.curreader=curreader


    def change_reader(self):
        """Propose to the user to select a reader or no reader, close the
current connection and open a new one with another reader"""

        readers=list(smartcard.System.readers()) # avoid side effects
        readers.append(self.READER_NULL)

        # pick a default reader
        i=len(readers)-1

        # DEBUG :  encountered problems while comparing readers and strings
        if isinstance(self.curreader, str):
            str_readers=[str(x) for x in readers]
            if self.curreader in str_readers:
                i=str_readers.index(self.curreader)
        else:
            if self.curreader in readers:
                i=readers.index(self.curreader)


        print "default", i #DEBUG
        curreader=selector(readers, i)[1]
        self.reset(curreader)


    def error_location(self, ustr, index):
        """returns the string appended with a newline and one indication of the
        given index

        the current implementation places an '^' right undex the caractec at the
        given index
        """
        # TODO : insert "@"+str(index) at the beginning of the "^" line if
        # there is enought space
        return ustr+"\n"+''.join([ ' ' for num in xrange(index)]) + "^"

    def normal_hex_input(self, ustr):
        """Parse a normal hexdecimal line of input

    Normal lines are formed of blocs whose length is even, and shortcut blocs
whose length is 1. Those shortcut blocs are equivalent to "0X", where X is
the shortcut bloc. The accepted character set is the set of all hexadcimal
characters.

    We return "" if the string doesn't contain any command, 
    or a string indicating a parsing error if there is one, 
    or the command, a list of bytes if given string is well-formed"""
        base=16 # hexa input
        
        command=[]
        for bloc in ustr.split():

            if len(bloc) % 2 == 1 and len(bloc) != 1: # don't accept blocs of 3, 5, ... 
                    # since user might forget a symbol if he doesn't split his
                    # command, but accept shortcuts for the high-order 0
                s="length of "+bloc+" is not even or equal to 1\n\n"
                m=re.search(escape_backslashes(bloc), ustr)
                s+=self.error_location(ustr, m.start())
                return s

            byte=0
            for i in xrange(len(bloc)):
                try:
                    value=int(bloc[i],base)
                except ValueError:
                    s="character "+bloc[i]+" is not an hexadecimal\n\n"
                    m=re.search(escape_backslashes(bloc), ustr)
                    s+=self.error_location(ustr, m.start()+i)
                    return s

                if len(bloc)== 1: # allows shortcuts for the high-order 0
                    byte=value
                    command.append(byte) # byte complete
                elif i % 2 ==0: # the first 4 bits of a byte of 2 symbols
                    byte=value*base
                else:
                    byte+=value
                    command.append(byte) # byte complete

        if len(command) == 0: # empty command
            return ""

        return command

    def push_zero_if_len1(self, x): 
        """ adds "0" in front of string if it's length is 1"""
        return len(x)==1 and "0"+x or x

    def autoconvert_data(self, data):
        """automatically convert list of bytes data to ascii char on some
conditions, return None if the default printing method should be applied

The current condition is whether it contains enough printable characters, but it
might be user-configured in the future"""
        pzero=self.push_zero_if_len1

        min_ascii=1.0 
            # minimal proportion of printable ascii characters in the data to
            # automatically enable translation
        
        len_few_errors=5
            # length needed to ensure a low probability of converting to ascii
            # non-ascii data
            # len_few_errors == 5 => probably less than 1% of errors
        ascii_chars=[chr(x) for x in data if 32 <= x <= 126 ]
            # only printable ascii characters

        if len(data) == 0: 
            return None

        if float(len(ascii_chars)) / len(data) >= min_ascii:
            out=[]
            for c in data:
                if 32 <= c <= 126:
                    out.append(chr(c))
                else: # display  unprintable as \xHH (not perfect but ok)
                    out.append('\\x'+pzero(hex(c)[2:]))

            asciistr=''.join(out)
            if len(asciistr) <= len_few_errors: 
                # still probable that data is not ascii data => print both
                asciistr+=" "+str([pzero(hex(x)[2:]) for x in ans])

            return asciistr


        else: # not enough evidence to print it in ascii
            return None

    def normal_hex_output(self, ans, sw1, sw2):
        """Format answer and the two status words nicely"""
        pzero=self.push_zero_if_len1

        data=self.autoconvert_data(ans)
        if data is None:
            data="["+(' '.join([pzero(hex(x)[2:]) for x in ans]))+"]"
        else:
            data="[ "+data+" ]"

        return data+" "+pzero(hex(sw1)[2:])+" "+pzero(hex(sw2)[2:])


    def fun_usrinput(self, ustr):
        """Parse and execute a line of input

        we return the string displayed by the cli, or None when we receive a
        commands that should trigger an exit of current shell.
        """
        ustr=self.remove_comments(ustr)

        if self.check_exit(ustr):
            if self.s is not None:
                self.s.close() # close connection
                self.s=None
            return None

        if len(ustr) >= 1 and ustr[-1] == '\\': # continuation on multiple lines
            self.command_acc+=ustr[:-1]
            return ""
        else:
            ustr=self.command_acc+ustr
            self.command_acc=""

        if len(ustr.split()) == 0: # empty command
            return ""

        # reset, changereader commands
        word_list=ustr.split()
        if "reset" == word_list[0]:
            self.reset()
            return "...Done"
        if "changereader" == word_list[0]:
            self.change_reader()
            return "...Current reader: "+str(self.curreader)

        # normal commands (sent to smartcard reader)
        command = self.normal_hex_input(ustr)
        if isinstance(command, str): # error or no command
            return command

        if self.s is not None:
            ans, sw1, sw2 = self.s.sendCommandAPDU(command)

            try: # error diagnosis. Excepts if there is an error
                self.errorchain[0](ans, sw1, sw2)
            except SWException, e:
                error_diagnosis=str(e)
            else:
                error_diagnosis=""

            return self.normal_hex_output(ans, sw1, sw2) + " " + error_diagnosis

        else: # no connection
            return "No connection : command was not sent"


    def check_exit(self, ustr):
        """Returns whether the current command line is an exit command"""
        if ustr is None:
            command=None
        else:
            words=ustr.split()
            command=len(words) > 0 and words[0] or ""

        if command in ["quit", "exit", None]:
            return True

        return False


    def remove_comments(self, ustr):
        """deletes any commented part of the string. Accepts None to tolerate
        EOF"""
        if ustr is None: # EOF
            return None

        comment_pattern='#'
        m=re.search(comment_pattern, ustr)
        if m:
            return ustr[:m.start()]
        else:
            return ustr

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                print "unable to read history file: "+histfile
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        try:
            readline.write_history_file(histfile)
        except IOError:
            pass


def usage():
    print """scriptim.py [option]
scriptim.py Copyright (C) 2011 Bernard Paulus; use option --license for more.
Options
-h
--help \t: print this help and exit
--license\t: print information about the license
More help can be found in the README.txt file"""
    
def license():
    print """
scriptim  Copyright (C) 2011 Bernard Paulus
This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.txt
This is free software, and you are welcome to redistribute it
under certain conditions; see LICENSE.txt for details. 
If LICENSE.txt is not present, refer to the GNU General Public License
Version 3 available at <http://www.gnu.org/licenses/>.
"""

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "license"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, arg in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o == "--license": 
            license()
            sys.exit()
        else:
            assert False, "unhandled option"

    print "scriptim.py Copyright (C) 2011 Bernard Paulus; use option --license\
 for more."
    c = fun_loop_creator()
    try:
        command_loop( c.fun_usrinput)
    except BaseException:
        if c is not None and c.s is not None:
            c.s.close()
        raise
    
    return 0


if  __name__ == "__main__":
    sys.exit(main())
