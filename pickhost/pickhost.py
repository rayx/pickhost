# Copyright (C) 2019 by Huan Xiong. All Rights Reserved.
# Licensed under GPLv3 or later. See LICENSE file under top level directory.


import configparser
import itertools
import os
import subprocess
from collections import OrderedDict
from pypick import Pick
from . import system

class Config:
    """
    Its instance represents a config file, which is either passed by
    caller, or a default one, based on XDG base directory specification.

    Args:
        os: OS object which provides config and cache dir location.
        file: User specified config file

    Attributes:
        file: Config file, either passed by user, or the default one.
        groups: data returned by parse(). It's an OrderedDict. Key is
            group name, value is hosts in that group.
    """
    def __init__(self, os, file=None):
        self.os = os
        if file:
            self.file = file
        else:
            self.file = self._get_config_file(create=True)

    def parse(self):
        """
        Parse config file and return an OrderedDict in which key is group
        name and value is hosts in that group.

        Returns:
            OrderedDict: its key is group name, value is hosts in that
                group.

        Raises:
            ValueError: Raised if failed to parse the file.
        """
        def _insert_after_parent(l, new_item):
            parent = None
            # First, Look for its parent. Then skip all existing children
            # of the parent. In other words, look for an item whose level
            # is same as or less than the parent and insert the item before
            # it.
            for index, item in enumerate(l):
                if not parent:
                    if item['name'] == new_item['_parent']:
                        parent = item
                else:
                    if item['_level'] <= parent['_level']:
                        l.insert(index, new_item)
                        break
            if parent and new_item not in l:
                l.append(new_item)
            if not parent:
                raise ValueError("Failed to find parent '%s' for '%s'" %
                                 (new_item['_parent'], new_item['name']))

        def _reorder(inlist, level, outlist):
            rest = []
            for i in inlist:
                if i['_level'] == level:
                    if not i['_parent']:
                        outlist.append(i)
                    else:
                        _insert_after_parent(outlist, i)
                else:
                    rest.append(i)
            if rest:
                _reorder(rest, level + 1, outlist)

        config = configparser.ConfigParser()
        with open(self.file) as f:
            config.read_file(itertools.chain(['[_global]'], f),
                             source=self.file)
        self.groups = OrderedDict()
        for section in config:
            entries = []
            for key, value in config[section].items():
                entries.append(self._parse_value(key, value))
            # Reorder hosts based on their parent/child relationship.
            self.groups[section] = []
            _reorder(entries, 0, self.groups[section])

        # 'DEFAULT' and '_global' are special sections. They don't appear
        # by default unless they have entries.
        if not self.groups['DEFAULT']:
            del self.groups['DEFAULT']
        if not self.groups['_global']:
            del self.groups['_global']
        return self.groups

    def _parse_value(self, name, value):
        """
        Parse option value, which has this format:
            <user>[!]@<host> [#<comment>]

        Args:
            name: Option name
            value: Option value

        Returns:
            dict: Contains the entry's fields.
        """
        entry = '%s = %s' % (name, value)

        def _get_name_and_parent(name):
            l = [i.strip() for i in name.split('->')]
            level = 0
            critical = False
            name = l[-1]
            # Set cirtical attribute if its name ends with '!'
            if name[-1] == '!':
                name = name[:-1]
                critical = True
            # Set its parent and level attirbute
            parent = None
            if len(l) > 1:
                parent = l[-2].replace('!', '')
                level = len(l) - 1
            return name, parent, level, critical

        def _get_user(value):
            # value format: <user>[!]@<host> [#<comment>]
            l = [i.strip() for i in value.split('@', 1)]
            if len(l) < 2:
                raise ValueError(entry)
            # The result contains two items: user and the rest part
            return l

        def _get_host_and_comment(value):
            if not value:
                raise ValueError(entry)
            l = [i.strip() for i in value.split('#', 1)]
            # Append a empty comment stirng if user doesn't specify one
            if len(l) == 1:
                l.append('')
            # The result contains two items: host and comment
            return l

        if not value:
            raise ValueError(entry)
        name, parent, level, critical = _get_name_and_parent(name)
        users, rest = _get_user(value)
        users = users.split(',')  # Convert it to list
        host, comment = _get_host_and_comment(rest)
        return {'name': name,
                'user': users,
                'host': host,
                'comment': comment,
                '_parent': parent,
                '_level': level,
                '_critical': critical}

    def _get_config_file(self, create=True):
        """Return the pathname of the default config file

        Args:
            create (boolean): if ture, create the file if it doesn't exist.

        Returns:
            str: pathname of the default config file.

        Raises:
            FileNotFoundError: Raised if the file doesn't exist and
                create flag is not True.
        """
        config_dir = self.os.config_dir()
        file = '%s/pickhost/hosts' % config_dir
        if os.path.exists(file):
            return file
        # If it reaches here, the file doesn't exist.
        if not create:
            raise FileNotFoundError(file)
        else:
            # Create the directory if it doesn't exist.
            dir = '%s/pickhost' % config_dir
            if not os.path.exists(dir):
                os.mkdir(dir)
            # Create an empty file.
            open(file, 'w').close()
            return file


class Cache:
    """
    Its instance represents a cache file, which contains only one entry
    (the last selected entry) in current implementation. Cache file is
    located based on XDG base directory specification. The function creates
    it if it doesn't exist.

    Args:
        os: OS object which provides config and cache dir location.
    """

    def __init__(self, os):
        self.os = os
        self.file = self._get_cache_file()

    def parse(self):
        """Parse the contents of cache file

        Returns:
            list: a list of entries
        """
        with open(self.file, 'r') as f:
            entry = f.read().strip()
        if not entry:
            return []
        name, user_and_host = [i.strip() for i in entry.split('=', 1)]
        user, host_and_desc = [i.strip() for i in user_and_host.split('@', 1)]
        host, desc = [i.strip() for i in host_and_desc.split('#', 1)]
        return [{'description': '%s: %s' % (desc, name),
                 'name': name,
                 'user': user,
                 'host': host,
                 '_critical': True}]

    def save_entry(self, entry, description):
        """
        Save an entry in cache file in this format:
            <name> = <user>@<host> #<description>
        Note it doesn't contains comments, "!", "->", etc, and user value
        must be a string (it can't be a list).
        """
        with open(self.file, 'w') as f:
            f.write('%s = %s@%s #%s' % (entry['name'], entry['user'],
                                        entry['host'], description))

    def _get_cache_file(self):
        """
        Return the pathname of cache file. The function creates it if
        it doesn't exist.

        Returns:
            str: pathname of cache file.
        """
        cache_dir = self.os.cache_dir()
        file = '%s/pickhost/hosts' % cache_dir
        if not os.path.exists(file):
            # Create the directory if it doesn't exist
            dir = '%s/pickhost' % cache_dir
            if not os.path.exists(dir):
                os.mkdir(dir)
            # Create an empty file
            open(file, 'w').close()
        return file


class PickHost(Pick):
    FIELDS = ['name', 'user', 'host', 'comment']
    FIELD_ATTS = {'name': {'width': 20},
                  'host': {'width': 20},
                  'user': {'width': 12},
                  'comment': {'return': False,
                              'style': 'trivial'}}

    CACHE_FIELDS = ['description']  # Showing this
    CACHE_EXTRA_FIELDS = ['name', 'user', 'host']  # Reurn these
    CACHE_FIELD_ATTS = {'description': {'return': False}}  # Not return this

    def __init__(self, file=None):
        super(PickHost, self).__init__(self.FIELDS,
                                       field_attrs=self.FIELD_ATTS)
        os = system.OS()
        # Get entries from cache file and add them to a specific group.
        self.cache = Cache(os)
        cached_entries = self.cache.parse()
        if cached_entries:
            group = self.create_group('', (self.CACHE_FIELDS,
                                           self.CACHE_EXTRA_FIELDS,
                                           self.CACHE_FIELD_ATTS))
            group.add_entries(cached_entries)

        # Config file contains multiple groups. Create and populate them.
        self.config = Config(os, file=file)
        for name, entries in self.config.parse().items():
            group = self.create_group(name)
            group.add_entries(entries)

    def run(self):
        entry = super(PickHost, self).run()
        # Save the result only when user selects an entry.
        if entry:
            self.cache.save_entry(entry, 'Last Accessed')
        return entry

    def edit(self):
        editor = self._get_editor()
        subprocess.call([editor, self.config.file])

    def _get_editor(self):
        # Return EDITOR if it's set.
        if 'EDITOR' in os.environ:
            editor = os.environ['EDITOR']
            if not os.path.isfile(editor):
                raise FileNotFoundError('EDITOR (%s)' % dir)
            return editor
        # Otherwise return vi
        editor = '/usr/bin/vi'
        if not os.path.isfile(editor):
            raise FileNotFoundError(editor)
        return editor
