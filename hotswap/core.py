'''
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the MIT License.

The full license is in the file COPYING.txt, distributed with this software.

Created on Sept 10, 2017

@author: jrm
'''
import sys
import enaml
from atom.api import AtomMeta, Instance, Subclass, set_default
from enaml.core.declarative import Declarative
from enaml.core.declarative_meta import DeclarativeMeta
from contextlib import contextmanager

from . import autoreload
from .autoreload import isinstance2


class EnamlReloader(autoreload.ModuleReloader):
    """ A class that takes two declarative trees
        and updates the first (old) with the second (new)

    """

    #: Original declarative View
    original = Instance(Declarative)

    #: Declarative view after reloading
    reloaded = Subclass(Declarative)

    #: Whether this reloader is enabled
    enabled = set_default(True)

    #: Autoreload all modules, not just those listed in 'modules'
    check_all = set_default(True)

    #: Add enaml as a source file type
    source_exts = set_default(['.py', '.enaml'])

    def check(self, check_all=False, do_reload=True):
        """Check whether some modules need to be reloaded."""
        with enaml.imports():
            super(EnamlReloader, self).check(check_all=check_all, do_reload=do_reload)


def update_member(old, new):
    """ Update an atom member """
    print("TODO: Update member {} {}".format(old, new))
    pass


def update_atom_members(old, new):
    """ Update an atom member """
    print("TODO: Update declarative {} {}".format(old, new))
    old_keys = old.members().keys()
    new_keys = new.members().keys()
    for key in old_keys:
        old_obj = getattr(old, key)
        try:
            new_obj = getattr(new, key)
            if old_obj == new_obj:
                continue
        except AttributeError:
            # Remove any obsolete members
            try:
                delattr(old, key)
            except (AttributeError, TypeError):
                pass
            continue

        try:
            #: Update any changed members
            setattr(old, key, getattr(new, key))
        except (AttributeError, TypeError):
            pass  # skip non-writable attributes

    #: Add any new members
    for key in set(new_keys)-set(old_keys):
        try:
            setattr(old, key, getattr(new, key))
        except (AttributeError, TypeError):
            pass  # skip non-writable attributes


def update_class_by_type(old, new):
    """ Update declarative classes or fallback on default """
    print("Update class by type {}, {}".format(old, new))
    autoreload.update_class(old, new)
    if isinstance2(old, new, AtomMeta):
        update_atom_members(old, new)


#: Add new rules for enaml
autoreload.UPDATE_RULES[0] = (lambda a, b: isinstance2(a, b, type), update_class_by_type)


class Hotswapper(autoreload.Autoreloader):

    def _default__reloader(self):
        return EnamlReloader(check_all=False)

    @contextmanager
    def active(self):
        self.pre_run_cell()
        yield
        self.post_execute()

    def update(self, old, new=None):
        """ Update given view declaration with new declaration"""

        #: Create and initialize
        if not new:
            new = type(old)()
            if not new.is_initialized:
                 new.initialize()

        #: Update attrs, funcs, and bindings
        self.update_attrs(old, new)
        self.update_funcs(old, new)
        self.update_bindings(old, new)

        #: Walk all children and find ones that "match"
        old_count, new_count = len(old.children), len(new.children)

        old_children = old.children[:]

        #: Add or remove any children
        for i, new_child in enumerate(new.children):
            name = new_child.__class__.__name__
            matches = [c for c in old_children if name==c.__class__.__name__]

            if matches:
                #: Update child
                #: TODO: We should pick the BEST one from this list
                #: based on some "matching" criteria (such as matching ref name or params)
                old_child = matches[0]
                old_children.remove(old_child)
                #: Update existing child
                self.update(old_child, new_child)

            else:
                #: New child, insert in place
                old.insert_children(i, [new_child])

        #: Destroy any removed children
        for c in old_children:
            if not c.is_destroyed:
                c.destroy()


    def update_attrs(self, old, new):
        #print("TODO: Update attrs {} {}".format(old, new))
        if new._d_storage:
            old._d_storage = new._d_storage
        #: TODO: Cannot add new attrs!

    def update_funcs(self, old, new):
        print("TODO: Update funcs {} {}".format(old, new))
        #if new._d_storage:
        #    old._d_storage = new._d_storage

    def update_bindings(self, old, new):
        print("TODO: Update bindings {} {}".format(old, new))
        if new._d_engine:
            old._d_engine = new._d_engine
            engine = old._d_engine

            #: Rerun any read expressions
            for k in engine._handlers.keys():
                try:
                    engine.update(old, k)
                except:
                    pass



