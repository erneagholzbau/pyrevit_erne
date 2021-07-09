# noinspection PyUnresolvedReferences
debug_mode = __forceddebugmode__

def dprint(*args, **kwargs):
    """
    prints args and kwargs only if the script
    cas called with debug ( ctrl + click )
    :param args:
    :param kwargs:
    :return:
    """
    if debug_mode:
        print(args, kwargs)
