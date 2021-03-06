# fork

```sh
pip install -e git+https://github.com/bmedicke/pykat.git#egg=pykat
```


PyKat
===========

PyKat is a wrapper for using FINESSE (http://www.gwoptics.org/finesse).
It aims to provide a Python toolset for automating more complex tasks
as well as providing a GUI for manipulating and viewing simulation
setups.

An article is available providing an overview of pykat: https://doi.org/10.1016/j.softx.2020.100613

Source code is hosted at https://git.ligo.org/finesse/pykat

Please cite pykat when used with::

    @article{BROWN_PYKAT,
        title = "Pykat: Python package for modelling precision optical interferometers",
        journal = "SoftwareX",
        volume = "12",
        pages = "100613",
        year = "2020",
        issn = "2352-7110",
        doi = "https://doi.org/10.1016/j.softx.2020.100613",
        url = "http://www.sciencedirect.com/science/article/pii/S2352711020303265",
        author = "Daniel D. Brown and Philip Jones and Samuel Rowlinson and Sean Leavey and Anna C. Green and Daniel Toyra and Andreas Freise",
    }


Examples and tutorials can be found at http://www.gwoptics.org/learn/

Please email `finesse-support@nikhef.nl` if you have any issues.



Installation
-------------

The easiest way to install PyKat is through Conda
(Recommended) or PyPi:
  
    conda install -c gwoptics pykat

    pip install pykat

The Conda installation has the advantage that it will also install the Finesse binaries too.

If you are a Windows user you also have the option to download the installer at https://pypi.python.org/pypi/PyKat.

You should now be able to open up a new Python terminal and type `import pykat`, the output should be::
    
    >>> import pykat
                                                  ..-
        PyKat 0.1              _                  '(
                              \`.|\.__...-""""-_." )
           ..+-----.._        /  ' `            .-'
       . '            `:      7/* _/._\    \   (
      (        '::;;+;;:      `-"' =" /,`"" `) /
      L.        \`:::a:f            c_/     n_'
      ..`--...___`.  .    ,
       `^-....____:   +.      www.gwoptics.org/pykat
    >>>

You will also need to ensure that you have a fully working copy of FINESSE installed and setup on your machine.
More details on this can be found at http://www.gwoptics.org/finesse. 

You must setup 2 environment variables: 'FINESSE_DIR', whose value is the directory that the 'kat' executable is in;
'KATINI', which states the directory and name of the kat.ini file to use by default in FINESSE, more information in the
FINESSE manual can be found about this.


Usage
------

This does not detail how to use FINESSE itself, just PyKat. FINESSE related queries should
be directed at the FINESSE manual or the mailing list  `finesse-support@nikhef.nl`

We highly recommend running PyKat with IPython or Jupyter Notebooks, it has so far provided the best way to explore the various PyKat objects and output data.
Also of use is IPythons interactive matplotlib mode - or pylab mode - which makes displaying and interacting with multiple plots easy.
You can start pylab mode from a terminal using::

    ipython -pylab

Regardless of which interpreter you use, to begin using PyKat you first need to include the following::

    from pykat import finesse
    from pykat.detectors import *
    from pykat.components import *
    from pykat.commands import *
    from pykat.structs import *

This provides all the various FINESSE components and commands you will typically need.
Running a simulation requires you to already know how to code FINESSE files, which is beyond
the scope of this readme. FINESSE commands can be entered in many ways: reading in a previous .kat
file, creating pykat objects representing the various FINESSE commands or by writing blocks of FINESSE code 
as shown next::

    import matplotlib.pyplot as plt

    # Here we write out any FINESSE commands we want to process
    code = """
    l l1 1 0 0 n1
    s s1 10 1 n1 n2
    m m1 0.5 0.5 0 n2 n3
    s s2 10 1 n3 n4
    m m2 0.5 0.5 0 n4 n5
    s s3 10 1 n5 n6

    pd pd_cav n4
    xaxis m1 phi lin 0 360 360
    yaxis abs:deg
    """

    # this kat object represents one single simulation, it containts
    # all the objects and their various states.
    kat = finesse.kat()
    
    # Currently the kat object is empty. We can fill it using a block
    # string of normal FINESSE commands by parsing them.
    kat.parse(code)
    
    # Once we have some simulation built up we can run it simply by calling...
    out = kat.run()

    # This out object contains the results from this run of the simulation.
    # Parameters can then be changed and kat.run() can be called again producing
    # another output object. So if we wanted to change the reflectivity of m1 we can do
    kat.m1.R = 0.2
    kat.m1.T = 0.8
    # now run it again...
    out2 = kat.run()
    
    # We can plot the output simply enough using pylab plotting.
    plt.figure()
    plt.plot(out.x, out["pd_cav"])
    plt.xlabel(out.xlabel)
    plt.ylabel("Intensity [W]")
    plt.legend(out.ylabels)
    plt.show()

The above demonstates a way of packaging up a FINESSE simulation - simple or complex - and 
including any post-processing and plotting in one Python script file. Or you can create
kat files separately and produce Python scripts to run and process them, that choice is upto
you, Pykat provides the means to be used in both ways.

To load in a separate FINESSE .kat file we can use the commands::
    
    kat = finesse.kat()
    # load in a separate file in the same directory...
    kat.load('test.kat')
    # the kat object has now parsed all the commands in this file.
    
    # We can alter and objects in there, e.g. if there was a mirror called m1
    kat.m1.phi = 45
    
    out = kat.run()
    
