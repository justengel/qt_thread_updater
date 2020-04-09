import threading

import qtpy
from qtpy import QtWidgets

from qt_thread_updater.thread_updater import ThreadUpdater


__all__ = ['get_updater', 'set_updater', 'cleanup_app',
           'get_global_updater_mngr', 'set_global_updater_mngr', 'GlobalUpdaterManager']


def get_updater():
    """Return the main updater. Override `GlobalUpdater.get_updater` to change how this function works.

    Overriding GlobalUpdater.get_updater may be needed if multiprocess/pickling does not work because of the lock.
    """
    return get_global_updater_mngr().get_updater()


def set_updater(updater):
    """Set the main updater. Override `GlobalUpdater.set_updater` to change how this function works."""
    get_global_updater_mngr().set_updater(updater)


def cleanup_app(app=None):
    """Clean up and delete the QApplication singleton."""
    if app is None:
        app = QtWidgets.QApplication.instance()

    # Reset the global reference to the updater
    set_updater(None)

    if app:
        app.closeAllWindows()
        for widg in app.allWindows():
            widg.deleteLater()

    for mod in dir(qtpy):
        try:
            delattr(getattr(qtpy, mod), 'qApp')
        except:
            pass
        try:
            setattr(getattr(qtpy, mod), 'qApp', None)
        except:
            pass


GLOBAL_UPDATER_MANGER = None


def get_global_updater_mngr():
    """Return the manager that creates and returns the ThreadUpdater."""
    global GLOBAL_UPDATER_MANGER
    return GLOBAL_UPDATER_MANGER


def set_global_updater_mngr(mngr):
    """Return the manager that creates and returns the ThreadUpdater."""
    global GLOBAL_UPDATER_MANGER
    GLOBAL_UPDATER_MANGER = mngr


class GlobalUpdaterManager(object):

    def __init__(self):
        self.lock = threading.RLock()
        self.main_updater = ThreadUpdater()

    def get_updater(self):
        """Return the main updater."""
        with self.lock:
            if self.main_updater is None:
                # Create a default updater (may cause issues if this is not created in the main thread)
                self.main_updater = ThreadUpdater(init_later=True)

                # Init later was temporarily used when the lock was not used. Two thread could create the main_updater
                # at the same time causing problems.
                # Initially I did not want to use a lock, because it could break multiprocessing for the module.
                self.main_updater.init()

            return self.main_updater

    def set_updater(self, updater):
        """Set the main updater."""
        with self.lock:
            self.main_updater = updater

    def __getstate__(self):
        """Return the variables to serialize. This should fix multiprocessing with locks pickling problems."""
        # Note do NOT give any lock objects!
        return {}

    def __setstate__(self, state):
        """Initialize this object in a separate process."""
        self.lock = threading.RLock()
        self.main_updater = ThreadUpdater()

        if isinstance(state, dict):
            for k, v in state.items():
                setattr(self, k, v)


# Set the default global updater manager
set_global_updater_mngr(GlobalUpdaterManager())
