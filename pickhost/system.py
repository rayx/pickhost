# Copyright (C) 2020 by Huan Xiong. All Rights Reserved.
# Licensed under GPLv3 or later. See LICENSE file under top level directory.


import os
import sys


class OS:
    """
    Provide config and cache file locations on different OSes.
    """
    def __init__(self):
        self.os = sys.platform
        self.home = os.environ['HOME']
        if self.os not in ['linux', 'darwin']:
            sys.stderr.write("The tool doesn't support the OS. Aborted.")
            sys.exit(1)

    def config_dir(self):
        if self.os == "linux":
            return self._linux_config_dir()
        elif self.os == "darwin":
            return self._darwin_config_dir()

    def _linux_config_dir(self):
        """
        Return XDG_CONFIG_HOME environment variable value if its set,
        otherwiese return its default value: $HOME/.config.

        Returns:
            str: User config dir.

        Raises:
            FileNotFoundError: Raised if XDG_CONFIG_HOME is set to a
                non-existant directory, or if $HOME/.config doesn't exist.
        """
        # Return XDG_CONFIG_HOME if it's set.
        if 'XDG_CONFIG_HOME' in os.environ:
            dir = os.environ['XDG_CONFIG_HOME']
            if not os.path.isdir(dir):
                raise FileNotFoundError('XDG_CONFIG_HOME (%s)' % dir)
            return dir
        # Otherwise return $HOME/.config
        dir = '%s/.config' % os.environ['HOME']
        if not os.path.isdir(dir):
            raise FileNotFoundError(dir)
        return dir

    def _darwin_config_dir(self):
        """
        Return ~/Library/Application Support/pickhost/config. Create it
        if it doesn't exist.

        Returns:
            str: User cache dir.
        """
        app_dir = '%s/Library/Application Support/pickhost' % self.home
        if not os.path.isdir(app_dir):
            os.mkdir(app_dir)
        config_dir = '%s/config' % app_dir
        if not os.path.isdir(config_dir):
            os.mkdir(config_dir)
        return config_dir

    def cache_dir(self):
        if self.os == "linux":
            return self._linux_cache_dir()
        elif self.os == "darwin":
            return self._darwin_cache_dir()

    def _linux_cache_dir(self):
        """
        Return XDG_CACHE_HOME environment variable value if its set,
        otherwiese return its default value: $HOME/.cache.

        Returns:
            str: User cache dir.

        Raises:
            FileNotFoundError: Raised if XDG_CACHE_HOME is set to a
                non-existant directory, or if $HOME/.cache doesn't exist.
        """
        # Return XDG_CACHE_HOME if it's set.
        if 'XDG_CACHE_HOME' in os.environ:
            dir = os.environ['XDG_CACHE_HOME']
            if not os.path.isdir(dir):
                raise FileNotFoundError('XDG_CACHE_HOME (%s)' % dir)
            return dir

        # Otherwise return $HOME/.cache, which is the default value of
        # XDG_CACHE_HOME.
        dir = '%s/.cache' % self.home
        if not os.path.isdir(dir):
            raise FileNotFoundError(dir)
        return dir

    def _darwin_cache_dir(self):
        """
        Return ~/Library/Application Support/pickhost/cache. Create it
        if it doesn't exist.

        Returns:
            str: User cache dir.
        """
        app_dir = '%s/Library/Application Support/pickhost' % self.home
        if not os.path.isdir(app_dir):
            os.mkdir(app_dir)
        cache_dir = '%s/cache' % app_dir
        if not os.path.isdir(cache_dir):
            os.mkdir(cache_dir)
        return cache_dir
