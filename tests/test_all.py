'''
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the MIT License.

The full license is in the file COPYING.txt, distributed with this software.

Created on Sept 10, 2017

@author: jrm
'''
import sys
from time import sleep

import pytest
import shutil
import enaml
from enaml.testing.utils import (close_all_windows, close_all_popups,
                                 handle_dialog, handle_question)
from enaml.widgets.api import PopupView, Window
from enaml.qt.qt_application import QtApplication
from enaml.core.declarative import Declarative
from hotswap.api import Hotswapper
from textwrap import dedent
from atom.api import Atom, Bool, Dict, Instance


class Test(Atom):
    #: Module object
    module = Instance(object)

    #: View instance
    view = Instance(Declarative)

    #: Reloaded state
    reloaded = Bool()

    #: Internal test state
    state = Dict()

    #: Set to true to stop the test
    done = Bool()

    #: Test result
    result = Bool(True)


# XXX add dedicated handlers for dynamics
def handle_conditional_example():
    """
    """
    pass


def handle_fields_example():
    """
    """
    pass


def handle_looper_example():
    """
    """
    pass


def handle_notebook_pages_example():
    """
    """
    pass


def handle_popup_view_example(app, window):
    """Test showing the popups.

    """
    def close_popup(app, popup):
        popup.central_widget().widgets()[-1].clicked = True

    popup_triggers = window.central_widget().widgets()
    with close_all_popups(app):
        with handle_dialog(app, handler=close_popup, skip_answer=True,
                           cls=PopupView):
            popup_triggers[0].clicked = True

        for t in popup_triggers[1:]:
            t.clicked = True
            app.process_events()


def handle_window_closing(app, window):
    """Test answering the question to close the window.

    """
    with handle_question(app, 'yes'):
        window.close()

    app.process_events()

    assert not Window.windows


def update_view(source, path='view.enaml'):
    """ Write the view to simulate a file change and delete the cache """
    try:
        #: Remove cache
        shutil.rmtree('__enamlcache__')
    except:
        pass

    #: Update file
    with open(path, 'w') as f:
        f.write(dedent(source))

DEFAULT_TIME = 0.5

def test_def_change():
    for test in run_hotswap_test(DEFAULT_TIME,
        original="""
            from enaml.widgets.api import *

            def talk():
                print("Meow")
                test.state['value'] = "Meow"

            enamldef Main(Window): view:
                Container:
                    PushButton:
                        clicked :: talk()
        """,
        modified="""
            from enaml.widgets.api import *

            def talk():
                print("Wolf")
                test.state['value'] = "Wolf"

            enamldef Main(Window): view:
                Container:
                    PushButton:
                        clicked :: talk()
        """,
        initial_state={
            'before':False,
            'after':False,
            'value':''
        }):

        #: This is freaking UGLY
        if not test.reloaded:
            if not test.state['before']:
                #: Before
                btn = test.view.children[0].children[0]
                btn.clicked()
                test.state['before'] = True
            else:
                assert test.state['value'] == "Meow"

        else:
            if not test.state['after']:
                #: Before
                btn = test.view.children[0].children[0]
                btn.clicked()
                test.state['after'] = True
            else:
                assert test.state['value'] == "Wolf"


def test_attr_change():
    for test in run_hotswap_test(DEFAULT_TIME,
         original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "initial"
            """,
         modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "reloaded"
            """,
         initial_state={}):

        text_view = test.view.children[0].children[0]
        if not test.reloaded:
            assert text_view.text == "initial"
        else:
            assert text_view.text == "reloaded"


def test_multiple_attr_change():
    for test in run_hotswap_test(DEFAULT_TIME,
                                 original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "initial"
            """,
                                 modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "reloaded"
                        align = "center"

            """,
                                 initial_state={}):

        text_view = test.view.children[0].children[0]
        if not test.reloaded:
            assert text_view.text == "initial"
        else:
            assert text_view.text == "reloaded"
            assert text_view.align == "center"


def test_subscription_change():
    for test in run_hotswap_test(2,
         original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label: label:
                        text = "test"
                    Label:
                        text << label.text
            """,
         modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label: label:
                        text = "test"
                    Label:
                        text << label.align
            """,
         initial_state={}):

        text_view = test.view.children[0].children[1]
        if not test.reloaded:
            assert text_view.text == "test"
        else:
            assert text_view.text == "left"


def test_subscription_ref_change():
    for test in run_hotswap_test(DEFAULT_TIME,
         original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label: label:
                        text = "test"
                    Label:
                        text << label.text


            """,
         modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label: label:
                        text = "test"
                    Label:
                        text << "{}".format(len(view.children))

            """,
         initial_state={}):

        text_view = test.view.children[0].children[1]
        if not test.reloaded:
            assert text_view.text == "test"
        else:
            assert text_view.text == "1"


def test_subscription_depdendent_change():
    for test in run_hotswap_test(DEFAULT_TIME,
         original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                title = "Hello"
                Container:
                    Label: label:
                        text << view.title
                    Label:
                        text << label.text


            """,
         modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                title = "New!"
                Container:
                    Label: label:
                        text << view.title * 2
                    Label:
                        text << label.text

            """,
         initial_state={}):

        tv1 = test.view.children[0].children[0]
        tv2 = test.view.children[0].children[1]
        if not test.reloaded:
            assert tv1.text == tv2.text == "Hello"
        else:
            assert tv1.text == tv2.text == "New!New!"


def test_attr_add_change():
    """ Test does not work because we can't add a member
        at runtime (get an attr error).
    """
    for test in run_hotswap_test(DEFAULT_TIME,
                                 original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "Hello"
            """,
                                 modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        attr awesome = True
                        text = "Hello"

            """,
                                 initial_state={}):

        tv1 = test.view.children[0].children[0]
        if not test.reloaded:
            assert tv1.get_member('awesome') is None
        else:
            assert tv1.get_member('awesome') == True


def test_append_child():
    """ """
    for test in run_hotswap_test(DEFAULT_TIME,
                                 original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "child 1"
            """,
                                 modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "child 1"
                    Label:
                        text = "child 2"

            """,
                                 initial_state={}):

        container = test.view.children[0]
        if not test.reloaded:
            assert len(container.children)==1
        else:
            assert len(container.children)==2
            tv1 = container.children[0]
            tv2 = container.children[1]
            assert tv1.text == "child 1" and tv2.text == "child 2"


def test_remove_child():
    """ """
    for test in run_hotswap_test(DEFAULT_TIME,
                                 original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "child 1"
                    Label:
                        text = "child 2"
            """,
                                 modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "child 2"

            """,
                                 initial_state={}):

        container = test.view.children[0]
        if not test.reloaded:
            assert len(container.children) == 2
        else:
            assert len(container.children) == 1
            tv1 = container.children[0]
            assert tv1.text == "child 2"



def test_swap_child():
    """ """
    for test in run_hotswap_test(DEFAULT_TIME+2,
                                 original="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    Label:
                        text = "child 1"
            """,
                                 modified="""
            from enaml.widgets.api import *

            enamldef Main(Window): view:
                Container:
                    PushButton:
                        text = "child 1"

            """,
                                 initial_state={}):

        container = test.view.children[0]
        if not test.reloaded:
            assert container.children[0].__class__.__name__ == 'Label'
        else:
            assert len(container.children) == 1
            assert container.children[0].__class__.__name__ == 'PushButton'


def run_hotswap_test(enaml_sleep, original, modified, handler=None, initial_state=None):
    """ Test the enaml examples.

    """
    qt_app = QtApplication.instance() or QtApplication()
    # Create a proper module in which to execute the compiled code so
    # that exceptions get reported with better meaning
    try:

        #: Write original view.enaml
        update_view(original)

        #: Import
        with enaml.imports():
            import view

        #: Create our hotswapper
        #: Must be done after importing our view!
        hotswapper = Hotswapper()
        #hotswapper.autoreload('2')

        with close_all_windows(qt_app):
            window = view.Main()
            window.show()
            window.send_to_front()

            #: Create our test "state"
            test = Test(module=view, view=window, reloaded=False, state=initial_state or {})

            #: Update our module with the test so we can access the state
            view.test = test

            #: Wait
            reload_sleep = enaml_sleep
            dt = 0.1
            while enaml_sleep > 0:
                qt_app.process_events()
                sleep(dt)
                yield test
                enaml_sleep -= dt

            update_view(modified)
            with hotswapper.active():
                #: We can run code here and it'll save any imported modules
                #: without having to do a full check
                #: Update our module with the test so we can access the state (if needed)
                view.test = test
                test.reloaded = True

                #: Update with our new code
                hotswapper.update(window)

            #: Wait again they should magically update!
            while reload_sleep > 0 and test.result and not test.done:
                qt_app.process_events()
                sleep(dt)
                #: Yield after reloading
                yield test
                reload_sleep -= dt

            if handler is not None:
               handler(qt_app, window)

            #: Check the test result
            assert test.result
    finally:
        pass
        # Make sure we clean up the sys modification before leaving
        del sys.modules['view']