LAST_STL_PATH = None

def set_last_stl(path):
    global LAST_STL_PATH
    LAST_STL_PATH = path

def get_last_stl():
    return LAST_STL_PATH
