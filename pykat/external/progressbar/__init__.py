#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# progressbar  - Text progress bar library for Python.
# Copyright (c) 2005 Nilton Volpato
# Copyright (c) 2012 Rick van Hattem
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


'''Text progress bar library for Python.

A text progress bar is typically used to display the progress of a long
running operation, providing a visual cue that processing is underway.

The ProgressBar class manages the current progress, and the format of the line
is given by a number of widgets. A widget is an object that may display
differently depending on the state of the progress bar. There are three types
of widgets:

 - a string, which always shows itself

 - a ProgressBarWidget, which may return a different value every time its
   update method is called

 - a ProgressBarWidgetHFill, which is like ProgressBarWidget, except it
   expands to fill the remaining width of the line.

The progressbar module is very easy to use, yet very powerful. It will also
automatically enable features like auto-resizing when the system supports it.
'''

from __future__ import division, absolute_import, with_statement

import math
import os
import signal
import sys
import time
from datetime import date
import six

try:
    from fcntl import ioctl
    from array import array
    import termios
except ImportError:  # pragma: no cover
    pass

try:
    from cStringIO import StringIO
except ImportError:  # pragma: no cover
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

from pykat.external.progressbar.widgets import *

__author__ = 'Rick van Hattem'
__author_email__ = 'Rick.van.Hattem@Fawo.nl'
__date__ = str(date.today())
__version__ = '2.7.3'


class UnknownLength:
    pass


class ProgressBar(object):

    '''The ProgressBar class which updates and prints the bar.

    A common way of using it is like:

    >>> pbar = ProgressBar().start()
    >>> for i in range(100):
    ...     pbar.update(i+1)
    ...     # do something
    ...
    >>> pbar.finish()

    You can also use a ProgressBar as an iterator:

    >>> progress = ProgressBar()
    >>> some_iterable = range(100)
    >>> for i in progress(some_iterable):
    ...     # do something
    ...     pass
    ...

    Since the progress bar is incredibly customizable you can specify
    different widgets of any type in any order. You can even write your own
    widgets! However, since there are already a good number of widgets you
    should probably play around with them before moving on to create your own
    widgets.

    The term_width parameter represents the current terminal width. If the
    parameter is set to an integer then the progress bar will use that,
    otherwise it will attempt to determine the terminal width falling back to
    80 columns if the width cannot be determined.

    When implementing a widget's update method you are passed a reference to
    the current progress bar. As a result, you have access to the
    ProgressBar's methods and attributes. Although there is nothing preventing
    you from changing the ProgressBar you should treat it as read only.

    Useful methods and attributes include (Public API):
     - currval: current progress (0 <= currval <= maxval)
     - maxval: maximum (and final) value
     - finished: True if the bar has finished (reached 100%)
     - start_time: the time when start() method of ProgressBar was called
     - seconds_elapsed: seconds elapsed since start_time and last call to
                        update
     - percentage(): progress in percent [0..100]
    '''

    _DEFAULT_MAXVAL = 100
    _DEFAULT_TERMSIZE = 80

    def __init__(self, maxval=None, widgets=None, term_width=None, poll=0.1,
                 left_justify=True, fd=sys.stderr, redirect_stderr=False,
                 redirect_stdout=False):
        '''Initializes a progress bar with sane defaults'''

        if widgets is None:
            # Don't share widgets with any other progress bars
            widgets = self.default_widgets()

        self.maxval = maxval
        self.widgets = widgets
        self.fd = fd
        self.left_justify = left_justify
        self.redirect_stderr = redirect_stderr
        self.redirect_stdout = redirect_stdout

        self.signal_set = False
        if term_width is not None:
            self.term_width = term_width
        else:
            try:
                self._handle_resize()
                signal.signal(signal.SIGWINCH, self._handle_resize)
                self.signal_set = True
            except (SystemExit, KeyboardInterrupt):  # pragma: no cover
                raise
            except:  # pragma: no cover
                self.term_width = self._env_size()

        self.__iterable = None
        self._update_widgets()
        self.currval = 0
        self.finished = False
        self.last_update_time = None
        self.poll = poll
        self.seconds_elapsed = 0
        self.start_time = None
        self.update_interval = 1

    def default_widgets(self):
        return [
            Percentage(), ' (', SimpleProgress(), ')', ' ', Bar(), ' ',
            Timer(), ' ', AdaptiveETA(),
        ]

    def __call__(self, iterable, maxval=None):
        'Use a ProgressBar to iterate through an iterable'
        if maxval is None:
            try:
                self.maxval = len(iterable)
            except:
                if self.maxval is None:
                    self.maxval = UnknownLength
        else:
            self.maxval = maxval

        self.__iterable = iter(iterable)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        try:
            value = next(self.__iterable)
            if self.start_time is None:
                self.start()
            else:
                self.update(self.currval + 1)
            return value
        except StopIteration:
            self.finish()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()

    def __enter__(self):
        return self.start()

    # Create an alias so that Python 2.x won't complain about not being
    # an iterator.
    next = __next__

    def __iadd__(self, value):
        'Updates the ProgressBar by adding a new value.'
        self.update(self.currval + value)
        return self

    def _env_size(self):
        'Tries to find the term_width from the environment.'

        return int(os.environ.get('COLUMNS', self._DEFAULT_TERMSIZE)) - 1

    def _handle_resize(self, signum=None, frame=None):
        'Tries to catch resize signals sent from the terminal.'

        h, w = array('h', ioctl(self.fd, termios.TIOCGWINSZ, '\0' * 8))[:2]
        self.term_width = w

    def percentage(self):
        'Returns the progress as a percentage.'
        return self.currval * 100.0 / (self.maxval or 1)

    percent = property(percentage)

    def _format_widgets(self):
        result = []
        expanding = []
        width = self.term_width

        for index, widget in enumerate(self.widgets):
            if isinstance(widget, WidgetHFill):
                result.append(widget)
                expanding.insert(0, index)
            else:
                widget = format_updatable(widget, self)
                result.append(widget)
                width -= len(widget)

        count = len(expanding)
        while count:
            portion = max(int(math.ceil(width * 1. / count)), 0)
            index = expanding.pop()
            count -= 1

            widget = result[index].update(self, portion)
            width -= len(widget)
            result[index] = widget

        return result

    def _format_line(self):
        'Joins the widgets and justifies the line'

        widgets = ''.join(self._format_widgets())

        if self.left_justify:
            return widgets.ljust(self.term_width)
        else:
            return widgets.rjust(self.term_width)

    def _need_update(self):
        'Returns whether the ProgressBar should redraw the line.'
        if self.currval >= self.next_update or self.finished:
            return True

        delta = time.time() - self.last_update_time
        return self._time_sensitive and delta > self.poll

    def _update_widgets(self):
        'Checks all widgets for the time sensitive bit'

        self._time_sensitive = any(getattr(w, 'TIME_SENSITIVE', False)
                                   for w in self.widgets)

    def update(self, value=None):
        'Updates the ProgressBar to a new value.'

        if value is not None and value is not UnknownLength:
            if (self.maxval is not UnknownLength
                    and not 0 <= value <= self.maxval
                    and not value < self.currval):

                raise ValueError('Value out of range')

            self.currval = value

        if self.start_time is None:
            self.start()
            self.update(value)
        if not self._need_update():
            return

        if self.redirect_stderr and sys.stderr.tell():
            self.fd.write('\r' + ' ' * self.term_width + '\r')
            self._stderr.write(sys.stderr.getvalue())
            self._stderr.flush()
            sys.stderr = StringIO()

        if self.redirect_stdout and sys.stdout.tell():
            self.fd.write('\r' + ' ' * self.term_width + '\r')
            self._stdout.write(sys.stdout.getvalue())
            self._stdout.flush()
            sys.stdout = StringIO()

        now = time.time()
        self.seconds_elapsed = now - self.start_time
        self.next_update = self.currval + self.update_interval
        
        if six.PY2:
            enc = self.fd.encoding
            if enc is None: enc = sys.getfilesystemencoding()
        
            self.fd.write('\r' + self._format_line().encode(enc, 'replace'))
        else:
            self.fd.write('\r' + self._format_line())
            
        self.last_update_time = now

    def start(self):
        '''Starts measuring time, and prints the bar at 0%.

        It returns self so you can use it like this:

        >>> pbar = ProgressBar().start()
        >>> for i in range(100):
        ...    # do something
        ...    pbar.update(i+1)
        ...
        >>> pbar.finish()
        '''

        if self.redirect_stderr:
            self._stderr = sys.stderr
            sys.stderr = StringIO()

        if self.redirect_stdout:
            self._stdout = sys.stdout
            sys.stdout = StringIO()

        if self.maxval is None:
            self.maxval = self._DEFAULT_MAXVAL

        self.num_intervals = max(100, self.term_width)
        self.next_update = 0

        if self.maxval is not UnknownLength:
            if self.maxval < 0:
                raise ValueError('Value out of range')
            self.update_interval = self.maxval / self.num_intervals

        self.start_time = self.last_update_time = time.time()
        self.update(0)

        return self

    def finish(self):
        'Puts the ProgressBar bar in the finished state.'

        self.finished = True
        self.update(self.maxval)
        self.fd.write('\n')
        if self.signal_set:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

        if self.redirect_stderr:
            self._stderr.write(sys.stderr.getvalue())
            sys.stderr = self._stderr

        if self.redirect_stdout:
            self._stdout.write(sys.stdout.getvalue())
            sys.stdout = self._stdout
