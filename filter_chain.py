#!/usr/bin/python


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

"""This file contains the classes to define a filter chain, and filter base
classes both for input and output"""

from scriptim_utils import *

# Design of the filter chain
# see original issue: https://github.com/bernardpaulus/scriptim/issues/8
#
# To recall, a filter chain is organised in zones. Each of those zones is
# delimited by a terminal filter. That filter transforms the data in another
# format. In other words, data in a zone possess some common characteristics
#
# A filter has two possibilities : execute an action (exit, send APDU, ...) or
# transform the input, passing it to the next module



class FilterChain:
    """FilterChain class is a list of Filters organized in zones.

Filters call the next level of treatment by calling the method
next(transformed_data)
"""
    def __init__(self):
        """Initialises attributes."""
        self.head=None
        self.tail=None
        self.zonedict={}

    def new_zone(self, name, terminal_filter):
        """creates a new zone, and append it to the current zones. The new zone
has the given filter as last filter of the zone.
the terminal filter should have no previous or next filter.
"""
        if not self.zonedict.has_key(name):
            raise DuplicateZoneName("a zone already has name : "+name)
        if self.head == None: # then tail is also None
            self.head = terminal_filter
            self.tail = terminal_filter
        else:
            terminal_filter.insert(self.tail, None)
            self.tail = terminal_filter
        self.zonedict[name] = terminal_filter

    def append_filter(self, zone_name, filter_obj):
        """appends a filter to the existing zone of that name, right before the
terminal filter of that zone.
"""
        terminal_filter = self.zonedict[zone_name]
        if terminal_filter is self.head:
            self.head = filter_obj
        filter_obj.insert(terminal_filter.prev, terminal_filter)

    def execute(self, data):
        """Execute the filter chain : feed the first filter with the data, which
will in turn feed the second, etc.
"""
        if self.head is not None:
            self.head.execute(data)


class List_Node:
    """A simple class for double linked list nodes"""
    def __init__(self):
        """Initialises attributes"""
        # avoid to deal with unset attributes
        self.prev=None
        self.next=None

    def insert(self, prevn=None, nextn=None):
        """insert this node between the two given node"""
        self.prev=prevn
        if self.prev is not None:
            self.prev.next=self
        self.next=nextn
        if self.next is not None:
            self.next.prev=self

    def remove(self):
        """remove the current Node from the list"""
        if self.prev is not None:
            self.prev.next=self.next
        if self.next is not None:
            self.next.prev=self.prev


class BaseFilter(List_Node):
    """Base class for every filter."""
    def execute(self, data):
        """apply this filter on the data. 

If this filter decides to execute some action (exit, sendAPDU, ...), it must
return.

On the contrary, if the data needs more treatment, it will call
self.exec_next() to propagate the data through the chain.

If everything goes correctly, the modules that decides to execute an action will
return something. This something will be propagated back through the chain, and
possibly modified.

If this filter encounter an error while processing the data, it will raise a
ProcessingException.

There is two kinds of processing errors: 
- the ones where the error can be pinpointed, for example when a user makes an
  error in his input,
- and the ones where we can't, like when we are unable to send a command because
  the reader is disconnected

When a module can pinpoint the origin of an error it must use an instance of
PinpointedError, a specialization of ProcessingException. 

The problem with this type of errors is that some filters might modify the
structure of the data. For the ones that do, it's their responsibility to trace
back the origin of the error in the data they initially received.

When a module can't pinpoint the origin of an error it must use an instance of
the more general ProcessingException.

Output and errors. Normal output should be 
"""
        return self.exec_next(data)

    def exec_next(self, data):
        """call the next filter on the data. Throws NoMoreFiltersException if
the current filter is the last
"""
        if self.next is not None:
            return self.next.execute(data)
        raise NoMoreFiltersException("this filter "+str(self)+"was the last one")


class IOmodule:
    """This class deals with inputs/output operations. It is used to
adapt the filter chain to either an """
