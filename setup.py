"""OpenMM command line script

This program sets up and runs an OpenMM simulation in a user-friendly
way.  It is roughly equivalent to to `grompp/mdrun` in Gromacs,
`dynamic` in Tinker, and `pmemd` in Amber.

To install this package, run `python setup.py install`. The only dependencies
are python and OpenMM.

For the short help, run `openmm -h`. To get help on all available options,
run `openmm --help-all`.

You need to provide coordinates and specify a force field.
Coordinates may come from a .pdb file.  Built-in protein force fields
and water models are shown in the help text, and you may add your own
OpenMM force field XML files.  Alternatively, you may provide AMBER
inpcrd/prmtop files.

You may provide simulation options through the command line; all
options are given in the help text.  Every time this program executes,
it makes a 'configuration file' which you may use as input for future
runs using the `--config` argument.  The command line options take
priority over those in the configuration file.  This provides a
convenient way to customize your default options.

Some nice features include:

1) Extensive validation of options and checking dependencies /
conflicts between options.

2) Reports your simulation progress, including speed in ns/day and
time left.

3) You may use units from simtk.unit on the command line when
specifying options with physical units.  

4) Suggestions are provided for typos on the command line.

5) Restart files that contain state information (coordinates,
velocities, and unit cell vectors) from the previous run.

This program is provided as an option for users to use OpenMM without
needing to write a Python script.  To take advantage of the full
flexibility of OpenMM as a domain-specific language for molecular
dynamics simulation, check out the OpenMM Script Builder located at
http://builder.openmm.org.
"""
DOCLINES = __doc__.split("\n")

import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
CLASSIFIERS = """\
Development Status :: 2 - alpha
Intended Audience :: Science/Research
"""

NAME                = 'openmm'
AUTHOR              = 'Lee-Ping Wang, Robert McGibbon'
AUTHOR_EMAIL        = "rmcgibbo@gmail.com"
DESCRIPTION         = DOCLINES[0]
LONG_DESCRIPTION    =  "\n".join(DOCLINES[2:])
LICENSE             = "BSD"
URL                 = 'https://github.com/rmcgibbo/openmm-cmd'
DOWNLOAD_URL        = 'https://github.com/rmcgibbo/openmm-cmd/releases'
PLATFORMS           = ['Windows', 'Linux', 'Mac OS-X', 'Solaris']
CLASSIFIERS         = filter(None, CLASSIFIERS.split('\n'))
VERSION             = '0.2'

SCRIPTS             = ['openmm']


def find_packages(extra_exclude=None):
    """Find all python packages inside the current directory by searching
    recursively through the directory tree, looking for directories with an
    __init__.py file in them.

    Parameters
    ----------
    extra_exclude : list, set
        Extra paths to add to the exclusion list.
    
    Returns
    -------
    packages : list
        A list of packages

    Examples
    --------
    >>> find_packages()
    ['ipcfg', 'ipcfg.IPython', 'ipcfg.IPython.decorator']
    """

    exclude = set(['.git', '.svn', 'build'])
    if extra_exclude is not None:
        exclude = exclude.union(extra_exclude)
        
    packages = []
    for dirpath, dirnames, filenames in os.walk('.'):
        # don't look in directories in exclude
        prune_indx = filter(lambda i: any(dirnames[i].endswith(e) for e in exclude),
                            range(len(dirnames)))
        # need to iterate in reverse order so that the indices don't get altered
        # as we're removing items
        for i in sorted(prune_indx)[::-1]:
            del dirnames[i]
        
        if '__init__.py' in filenames:
            packages.append(os.path.relpath(dirpath, '.').replace('/', '.'))

    return packages


if __name__ == '__main__':
    setup(name=NAME,
          scripts=SCRIPTS,
          packages=find_packages(),
          version=VERSION,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          license=LICENSE,
          url=URL,
          download_url=DOWNLOAD_URL,
          platforms=PLATFORMS,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION)
