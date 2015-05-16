#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Library functions for compiling the grammar files."""

import json
import os
import plistlib
import re
import sys
import traceback


def iter_tree_dicts(tree, initpath=u''):
    """Iterate over the tree entries."""
    stack = []
    stack.append((initpath, tree))
    while stack:
        (path, obj) = stack.pop()
        if isinstance(obj, list):
            for idx, elem in enumerate(obj):
                np = u'[%d]' % idx
                stack.append((path + np, obj[idx]))
        elif isinstance(obj, dict):
            yield (path, obj)
            for (k, v) in obj.iteritems():
                np = u'/' + k
                stack.append((path + np, v))


class CompilerError(ValueError):

    """CompilerError is raised when compilation fails."""

    pass


class TokenReplacement:

    """TokenReplacement handles token replacement."""

    @classmethod
    def run(cls, grammar):
        """Process the given grammar."""
        if u'tokens' in grammar:
            instance = cls(grammar[u'tokens'])
            result = instance.in_grammar(grammar)
            instance.print_counts()
            del grammar[u'tokens']
            return result
        else:
            print('No "tokens" in grammar.')
            return grammar

    def __init__(self, token_dict):
        """Construct a new TokenReplacement instance."""
        self.token_dict = token_dict
        self.replace_counts = {}
        for k in token_dict:
            self.replace_counts[k] = 0

    def in_string(self, value, path):
        """Replace tokens in a string."""
        def replacement(match):
            name = match.group(1)
            if name in self.token_dict:
                self.replace_counts[name] += 1
                return u'(?:' + self.token_dict[name] + u')'
            else:
                msg = u'Reference to undefined token: "%s" at %s' % (name, path)
                raise CompilerError(msg)

        return re.sub(u'⟪([^⟫]*)⟫', replacement, value)

    def in_tree(self, tree, initpath):
        """Replace tokens in a tree."""
        for (path, node) in iter_tree_dicts(tree, initpath):
            for (k, v) in node.iteritems():
                if k in [u'begin', u'end', u'match']:
                    itempath = path + u'/' + k
                    node[k] = self.in_string(v, itempath)

    def in_grammar(self, grammar):
        """Replace tokens in a grammar."""
        self.in_tree(grammar.get(u'patterns', []), u'/patterns')
        for (name, r_item) in grammar.get(u'repository', {}).iteritems():
            self.in_tree(r_item, u'/repository/' + name)

    def print_counts(self):
        """Print the token counts."""
        for (t, n) in self.replace_counts.iteritems():
            print('Replaced %d occurrences of %s.' % (n, t))


class IncludeCheck:

    """IncludeCheck checks for includes."""

    @classmethod
    def run(cls, grammar):
        """Process the given grammar."""
        cls(grammar).check_includes()
        return grammar

    def __init__(self, grammar):
        """Construct a new instance of IncludeCheck."""
        self.grammar = grammar
        self.repository = grammar.get(u'repository', {})
        self.grammar_includes = set()
        self.repo_includes = dict([(k, set()) for k in self.repository])

    def check_includes(self):
        """Check for includes."""
        patterns = self.grammar.get(u'patterns', [])
        for (path, node) in iter_tree_dicts(patterns, u'/patterns'):
            if u'include' in node:
                self.add_include(node[u'include'], self.grammar_includes, path)
        for (name, item) in self.repository.iteritems():
            for (path, node) in iter_tree_dicts(item, u'/repository/' + name):
                if u'include' in node:
                    incset = self.repo_includes[name]
                    self.add_include(node[u'include'], incset, path)
        self.print_unused()

    def add_include(self, name, set, path):
        """Add an include."""
        if name.startswith('#'):
            item = name[1:]
            if item in self.repository:
                set.add(item)
            else:
                msg = u'Undefined repository item "%s" at %s' % (item, path)
                raise CompilerError(msg)

    def print_unused(self):
        """Print any unused items."""
        for item in self.unused_items():
            print(u'Repository item "%s" is not used.' % item)

    def unused_items(self):
        """Return the set of unused items."""
        used = set()
        for item in self.grammar_includes:
            used |= self.usage_closure(item, used)
        return set(self.repository) - used

    def usage_closure(self, item, closure=None):
        """Find used items."""
        if not closure:
            closure = set()
        if item not in closure:
            closure.add(item)
            for used_item in self.repo_includes[item]:
                closure |= self.usage_closure(used_item, closure)
        return closure


def xml_filename(json_file):
    """Translate the JSON file name to an XML file name."""
    path, fname = os.path.split(json_file)
    fbase, old_ext = os.path.splitext(fname)
    return os.path.join(path, fbase + '.tmLanguage')


def build(json_file):
    """Perform the build."""
    grammar = None
    try:
        with open(json_file) as json_content:
            grammar = json.load(json_content)
    except ValueError as e:
        print("Error parsing JSON in %s:\n  %s" % (json_file, e))
    else:
        for op in [TokenReplacement, IncludeCheck]:
            try:
                op.run(grammar)
            except CompilerError as e:
                print(u'Error during %s:\n  %s' % (op.__name__, e))
                return None
            except Exception:
                traceback.print_exc()
                return None

        plistlib.writePlist(grammar, xml_filename(json_file))


if __name__ == "__main__":
    build(sys.argv[1])
