import os

def remove_file(filename):
    if os.path.exists(filename):
        os.remove(filename)

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def file_exists(filename):
    return os.path.exists(filename)
