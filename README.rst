===============================================================================
Parser and GUI viewer of chatsync/\*.dat files from the Skype profile directory
===============================================================================

Skype stores conversations locally in two places. One is a SQLite database file, for which there are several convenient viewers out there.
Another is a set of ``dat`` files in the ``chatsync`` subdirectory of the profile. The latter contain, among other things, the "removed" messages 
along with all the edits. Unfortunately, the format of those dat files does not seem to be documented anywhere, and the readers are scarce.

The package contains a crude file format parser for the ``dat`` files in the ``chatsync`` directory, created based on the hints,
given by user *kmn* in `this discussion <http://www.hackerfactor.com/blog/index.php?/archives/231-Skype-Logs.html#c1066>`__.

As the format specification used is not official and incomplete, the parser is limited in what it can do.
It may fail on some files, and on other files will only be able to extract messages partially.

In addition, the package contains a simple wx-based GUI tool for searching the log files visually.

.. image:: http://fouryears.eu/wp-content/uploads/2015/01/skype-chatsync-viewer.png
   :align: center
   :target: http://fouryears.eu/2015/01/22/skype-removed-messages/

Installation
------------

The easiest way to install most Python packages is via ``easy_install`` or ``pip``::

    $ easy_install skype_chatsync_reader
    
If you want to use the GUI tool, you will also need to install `wxPython 2.8 <http://wxpython.org/>`__ or later (it is not installed automatically).

Usage
-----

If you want to parse chatsync files programmatically, check out the ``SkypeChatSyncScanner`` and ``SkypeChatSyncParser`` classes in ``skype_chatsync_reader.scanner``.
A typical usage example is::

    with open(dat_file, 'rb') as f:
        s = SkypeChatSyncScanner(f)
        s.scan()
        p = SkypeChatSyncParser(s)
        p.parse()
    
Then use ``p.timestamp``, ``p.participants``, and ``p.conversation`` to read out the messages. There convenience function ``parse_chatsync_profile_dir`` will scan 
through all the ``dat`` files in the provided ``chatsync`` dir and parse all of them (which can be parsed).

If you want to use the GUI tool, simply run the script::
    
    $ skype-chatsync-viewer

which is installed into your python's scripts directory together with the package.


Issues
------

This is a very crude implementation, written up in a single evening for fun. It is not meant to be production-quality software. There are numerous known and unknown issues.
I do not plan to maintain this actively. Feel free to contribute via `Github <http://github.org/konstantint/skype-chatsync-reader>`__.


Copyright
---------

 * Copyright 2015, `Konstantin Tretyakov <http://kt.era.ee/>`__
 * MIT License
 * The icon used in the single-file executable is (c) `Umut Pulat <http://www.iconarchive.com/show/tulliana-2-icons-by-umut-pulat/log-icon.html>`__, licensed under LGPL.