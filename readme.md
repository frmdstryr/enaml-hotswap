### enaml-hotswap

Hotswap enaml views like react native's hot-swapping.  Hook into your code, make a change and watch
the UI update in place!  Based on IPython's [autoreloader](https://github.com/ipython/ipython/blob/master/IPython/extensions/autoreload.py)

Built for [enaml-native](https://www.codelv.com/projects/enaml-native/) but is done at the declarative
level so it should work any enaml views.
 
#### What can it do?

See the `tests/test_all.py` for examples. 

It can do things such as updating attributes and bindings on the fly (can't add or remove attr's
at the moment), add or remove nodes, and swap out functions.
   



