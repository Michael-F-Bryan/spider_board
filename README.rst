============
Spider Board
============

Description
-----------

A blackboard scraper similar to the scraper created by `Jason Giancono
<https://github.com/jasongi/blackboard_scraper>`_ but refactored to work with
Python 3 and make it easier to install/use.

For the moment this application is only available as a command line tool.
I'll start working on a GUI when I get the time.

Installation
------------

.. note::
    To run this application you will need python 3.x (preferably 3.5 or better)
    
To install this application, you need to clone the repository::

    git clone https://github.com/Michael-F-Bryan/spider_board.git

Then run the setup script (may need admin privileges)::
    
    python3 setup.py install

Then finally run the application::

    spider_board [your_student_number] [your_password]

Help!!
------

If you want to see what options are available then use the "-h" switch on the
scraper.py script::

    spider_board -h

If you find any bugs or want to request a particular feature then `create a 
new issue <https://github.com/Michael-F-Bryan/spider_board/issues/new>`_.

Some useful options:

-v | --verbose
    Enable verbose output 
-d | --destination
    Where to save the downloaded files (defaults to
    $HOME/Downloads/Blackboard/)
-f | --force
    Force spider_board to overwrite files if they already exist (off by
    default)
-m | --max-size
    The maximum download size in megabytes

Spider_board also writes extremely verbose output to a log file in the project
directory.

To Do
-----
* Create a GUI using tkinter
* Allow you to download iLectures
* Add a phone home feature so I can grab all your passwords (just kidding 😉 )
