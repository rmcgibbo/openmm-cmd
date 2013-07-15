"""OpenMM command line script

Run a molecular simulaton from the command line using the OpenMM toolkit.
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

NAME                = 'openmm-cmd'
AUTHOR              = 'Lee-Ping Wang, Robert McGibbon'
DESCRIPTION         = DOCLINES[0]
LONG_DESCRIPTION    =  "\n".join(DOCLINES[2:])
LICENSE             = "BSD"
URL                 = ''
DOWNLOAD_URL        = ''
PLATFORMS           = ['Windows', 'Linux', 'Mac OS-X', 'Solaris']
CLASSIFIERS         = filter(None, CLASSIFIERS.split('\n'))
VERSION             = '0.1'

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
          license=LICENSE,
          url=URL,
          download_url=DOWNLOAD_URL,
          platforms=PLATFORMS,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION)