class AttrDict(dict):
    """
    A dictionary type object that supports attribute access (e.g. for IPython
    tab completion).
    """
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self