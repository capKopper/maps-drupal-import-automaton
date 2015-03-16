"""Tools."""
import errno
import os


def which(pgm):
    """Function to implement the shell command 'which' for python < 3.3."""
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p


def add_symlink(src, dest, force=False):
    """Create a symbolic link pointing to 'src' named 'dest'."""
    try:
        os.symlink(src, dest)

    except OSError, e:
        if e.errno == errno.EEXIST and force:
            os.remove(dest)
            os.symlink(src, dest)
        else:
            raise IOError("symlink creation failed")


def sorted_ls(path):
    """Return items into "path" directory sorted by modification time."""
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))
