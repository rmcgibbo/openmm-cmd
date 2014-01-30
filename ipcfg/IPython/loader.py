"""A simple configuration system.

Inheritance diagram:

.. inheritance-diagram:: IPython.config.loader
   :parts: 3

Authors
-------
* Brian Granger
* Fernando Perez
* Min RK
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import argparse
import copy
import os
import re
import sys
import json

from ipcfg.IPython.path import filefind
from ipcfg.IPython import py3compat
from ipcfg.IPython.py3compat import unicode_type, iteritems
from ipcfg.IPython.traitlets import HasTraits, List, Any, TraitError
DEFAULT_ENCODING = sys.getdefaultencoding()

#-----------------------------------------------------------------------------
# Exceptions
#-----------------------------------------------------------------------------


class ConfigError(Exception):
    pass

class ConfigLoaderError(ConfigError):
    pass

class ConfigFileNotFound(ConfigError):
    pass

class ArgumentError(ConfigLoaderError):
    pass

class AliasError(AttributeError):
    def __init__(self, lhs, aliases):
        import difflib
        closest = difflib.get_close_matches(lhs, aliases.keys(), n=1)
        if len(closest) == 0:
            self.msg = "Unrecognized option: '%s'." %  lhs
        else:
            self.msg = "Unrecognized option: '%s'. Did you mean '%s'?" % \
                (lhs, closest[0])

    def __str__(self):
        return self.msg

#-----------------------------------------------------------------------------
# Argparse fix
#-----------------------------------------------------------------------------

# Unfortunately argparse by default prints help messages to stderr instead of
# stdout.  This makes it annoying to capture long help screens at the command
# line, since one must know how to pipe stderr, which many users don't know how
# to do.  So we override the print_help method with one that defaults to
# stdout and use our class instead.

class ArgumentParser(argparse.ArgumentParser):
    """Simple argparse subclass that prints help to stdout by default."""

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        return super(ArgumentParser, self).print_help(file)

    print_help.__doc__ = argparse.ArgumentParser.print_help.__doc__

#-----------------------------------------------------------------------------
# Config class for holding config information
#-----------------------------------------------------------------------------

class LazyConfigValue(HasTraits):
    """Proxy object for exposing methods on configurable containers
    
    Exposes:
    
    - append, extend, insert on lists
    - update on dicts
    - update, add on sets
    """
    
    _value = None
    
    # list methods
    _extend = List()
    _prepend = List()
    
    def append(self, obj):
        self._extend.append(obj)
    
    def extend(self, other):
        self._extend.extend(other)
    
    def prepend(self, other):
        """like list.extend, but for the front"""
        self._prepend[:0] = other
    
    _inserts = List()
    def insert(self, index, other):
        if not isinstance(index, int):
            raise TypeError("An integer is required")
        self._inserts.append((index, other))
    
    # dict methods
    # update is used for both dict and set
    _update = Any()
    def update(self, other):
        if self._update is None:
            if isinstance(other, dict):
                self._update = {}
            else:
                self._update = set()
        self._update.update(other)
    
    # set methods
    def add(self, obj):
        self.update({obj})
    
    def get_value(self, initial):
        """construct the value from the initial one
        
        after applying any insert / extend / update changes
        """
        if self._value is not None:
            return self._value
        value = copy.deepcopy(initial)
        if isinstance(value, list):
            for idx, obj in self._inserts:
                value.insert(idx, obj)
            value[:0] = self._prepend
            value.extend(self._extend)
        
        elif isinstance(value, dict):
            if self._update:
                value.update(self._update)
        elif isinstance(value, set):
            if self._update:
                value.update(self._update)
        self._value = value
        return value
    
    def to_dict(self):
        """return JSONable dict form of my data
        
        Currently update as dict or set, extend, prepend as lists, and inserts as list of tuples.
        """
        d = {}
        if self._update:
            d['update'] = self._update
        if self._extend:
            d['extend'] = self._extend
        if self._prepend:
            d['prepend'] = self._prepend
        elif self._inserts:
            d['inserts'] = self._inserts
        return d


def _is_section_key(key):
    """Is a Config key a section name (does it start with a capital)?"""
    if key and key[0].upper()==key[0] and not key.startswith('_'):
        return True
    else:
        return False


class Config(dict):
    """An attribute based dict that can do smart merges."""

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self._ensure_subconfig()
    
    def _ensure_subconfig(self):
        """ensure that sub-dicts that should be Config objects are
        
        casts dicts that are under section keys to Config objects,
        which is necessary for constructing Config objects from dict literals.
        """
        for key in self:
            obj = self[key]
            if _is_section_key(key) \
                    and isinstance(obj, dict) \
                    and not isinstance(obj, Config):
                setattr(self, key, Config(obj))
    
    def _merge(self, other):
        """deprecated alias, use Config.merge()"""
        self.merge(other)
    
    def merge(self, other):
        """merge another config object into this one"""
        to_update = {}
        for k, v in iteritems(other):
            if k not in self:
                to_update[k] = copy.deepcopy(v)
            else: # I have this key
                if isinstance(v, Config) and isinstance(self[k], Config):
                    # Recursively merge common sub Configs
                    self[k].merge(v)
                else:
                    # Plain updates for non-Configs
                    to_update[k] = copy.deepcopy(v)

        self.update(to_update)

    def __contains__(self, key):
        # allow nested contains of the form `"Section.key" in config`
        if '.' in key:
            first, remainder = key.split('.', 1)
            if first not in self:
                return False
            return remainder in self[first]
        
        return super(Config, self).__contains__(key)
    
    # .has_key is deprecated for dictionaries.
    has_key = __contains__
    
    def _has_section(self, key):
        return _is_section_key(key) and key in self
    
    def copy(self):
        return type(self)(dict.copy(self))

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        import copy
        return type(self)(copy.deepcopy(list(self.items())))
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if _is_section_key(key):
                c = Config()
                dict.__setitem__(self, key, c)
                return c
            else:
                # undefined, create lazy value, used for container methods
                v = LazyConfigValue()
                dict.__setitem__(self, key, v)
                return v

    def __setitem__(self, key, value):
        if _is_section_key(key):
            if not isinstance(value, Config):
                raise ValueError('values whose keys begin with an uppercase '
                                 'char must be Config instances: %r, %r' % (key, value))
        dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        if key.startswith('__'):
            return dict.__getattr__(self, key)
        try:
            return self.__getitem__(key)
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        if key.startswith('__'):
            return dict.__setattr__(self, key, value)
        try:
            self.__setitem__(key, value)
        except KeyError as e:
            raise AttributeError(e)

    def __delattr__(self, key):
        if key.startswith('__'):
            return dict.__delattr__(self, key)
        try:
            dict.__delitem__(self, key)
        except KeyError as e:
            raise AttributeError(e)


#-----------------------------------------------------------------------------
# Config loading classes
#-----------------------------------------------------------------------------


class ConfigLoader(object):
    """A object for loading configurations from just about anywhere.

    The resulting configuration is packaged as a :class:`Config`.

    Notes
    -----
    A :class:`ConfigLoader` does one thing: load a config from a source
    (file, command line arguments) and returns the data as a :class:`Config` object.
    There are lots of things that :class:`ConfigLoader` does not do.  It does
    not implement complex logic for finding config files.  It does not handle
    default values or merge multiple configs.  These things need to be
    handled elsewhere.
    """

    def _log_default(self):
        from IPython.config.application import Application
        return Application.instance().log

    def __init__(self, log=None):
        """A base class for config loaders.

        log : instance of :class:`logging.Logger` to use.
              By default loger of :meth:`IPython.config.application.Application.instance()`
              will be used

        Examples
        --------

        >>> cl = ConfigLoader()
        >>> config = cl.load_config()
        >>> config
        {}
        """
        self.clear()
        if log is None:
            self.log = self._log_default()
            self.log.debug('Using default logger')
        else:
            self.log = log

    def clear(self):
        self.config = Config()

    def load_config(self):
        """Load a config from somewhere, return a :class:`Config` instance.

        Usually, this will cause self.config to be set and then returned.
        However, in most cases, :meth:`ConfigLoader.clear` should be called
        to erase any previous state.
        """
        self.clear()
        return self.config


class FileConfigLoader(ConfigLoader):
    """A base class for file based configurations.

    As we add more file based config loaders, the common logic should go
    here.
    """

    def __init__(self, filename, path=None, **kw):
        """Build a config loader for a filename and path.

        Parameters
        ----------
        filename : str
            The file name of the config file.
        path : str, list, tuple
            The path to search for the config file on, or a sequence of
            paths to try in order.
        """
        super(FileConfigLoader, self).__init__(**kw)
        self.filename = filename
        self.path = path
        self.full_filename = ''

    def _find_file(self):
        """Try to find the file by searching the paths."""
        self.full_filename = filefind(self.filename, self.path)

