class RootFinderMixin(object):

    def __init__(self, root_widget_class='RootWidget'):
        self.root_widget_class = root_widget_class

    def find_root(self):
        root = self.parent
        while root.__class__.__name__ != self.root_widget_class:
            root = root.parent
        return root
