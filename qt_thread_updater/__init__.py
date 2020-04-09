"""
Thread Updater module to help update GUI items in a separate thread.
"""
from .__meta__ import version as __version__

import sys
import threading
import traceback
import contextlib
from collections import OrderedDict

import qtpy
from qtpy import QtCore, QtWidgets


__all__ = ['get_updater', 'set_updater', 'cleanup_app', 'ThreadUpdater']


MAIN_UPDATER = None


def get_updater():
    """Return the main updater."""
    global MAIN_UPDATER

    if MAIN_UPDATER is None:
        # Create a default updater
        # (may error in separate thread ... Solved with moveToThread below)
        MAIN_UPDATER = ThreadUpdater()

    return MAIN_UPDATER


def set_updater(updater):
    """Set the main updater."""
    global MAIN_UPDATER
    MAIN_UPDATER = updater


def cleanup_app(app=None):
    """Clean up and delete the QApplication singleton."""
    if app is None:
        app = QtWidgets.QApplication.instance()

    # Remove the global reference to the updater
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


class ThreadUpdater(QtCore.QObject):
    """General timer that will call functions on an interval.

    DEBUG Types:

        * PRINT_ERROR ["print"]: If an error occurs print the traceback to stderr.
        * HIDE_ERROR ["hide"]: If an error occurs ignore it and do not display the error.
        * RAISE_ERROR ["raise"]: If an error occurs actually raise the error. This will crash the updater.

    Args:
         timeout (float/int)[1/30]: Interval in which to run the update functions (in seconds).
         debug_type (str)[PRINT_ERROR]: Control to manage how errors are handled.
         parent (QtCore.QObject)[None]: Parent QObject.
    """

    starting = QtCore.Signal()  # Signal to start the timer in the main thread.
    stopping = QtCore.Signal()  # Signal to stop the timer in the main thread.
    creating = QtCore.Signal()  # Signal to create the timer in the main thread.

    PRINT_ERROR = 'print'  # Print to stderr
    HIDE_ERROR = 'hide'    # Do nothing and hide the error
    RAISE_ERROR = 'raise'  # Crash the update function and raise the error

    def __init__(self, timeout=1/30, debug_type=PRINT_ERROR, parent=None):
        """Initialize the ThreadUpdater.

        Args:
             timeout (float/int)[1/30]: Interval in which to run the update functions (in seconds).
             debug_type (str)[PRINT_ERROR]: Control to manage how errors are handled.
             parent (QtCore.QObject)[None]: Parent QObject.
        """
        super().__init__(parent)

        # Lock and update variables
        self._call_latest = OrderedDict()
        self._latest_lock = threading.Lock()
        self._call_in_main = OrderedDict()
        self._main_lock = threading.Lock()
        self._always_call = OrderedDict()
        self._always_lock = threading.Lock()

        # Control variables
        self._timeout = timeout
        self.debug_type = debug_type
        self._running = False
        self._tmr = None

        # Move to main thread before connecting the signals, so signals run in the main thread
        if threading.current_thread() != threading.main_thread():
            self.moveToThread(QtWidgets.QApplication.instance().thread())

        # Connect the signals
        self.starting.connect(self.start)
        self.stopping.connect(self.stop)
        self.creating.connect(self.create_timer)

        # Create the timer
        self.create_timer()

    @contextlib.contextmanager
    def handle_error(self, func=None):
        """Context manager to handle exceptions if the unknown update functions cause an error.

        Change how the errors are handled with the "debug_type" variable.
          * PRINT_ERROR ["print"]: If an error occurs print the traceback to stderr.
          * HIDE_ERROR ["hide"]: If an error occurs ignore it and do not display the error.
          * RAISE_ERROR ["raise"]: If an error occurs actually raise the error. This will crash the updater.
        """
        if self.debug_type == self.RAISE_ERROR:
            yield  # If this errors it will crash the updater and raise teh real error.
        elif self.debug_type == self.HIDE_ERROR:
            try:
                yield
            except Exception:
                pass
        else:  # self.debug_type == self.PRINT_ERROR:
            try:
                yield
            except Exception:
                traceback.print_exc()
                print('Error in {}'.format(func.__name__), file=sys.stderr)

    @contextlib.contextmanager
    def restart_on_change(self, restart=None):
        """Context manager to stop and restart the timer if it is running."""
        if restart is None:
            restart = self.is_running()
        if restart:
            self.stop()
            yield
            self.start()
        else:
            yield

    def get_timeout(self):
        """Return the update timer interval in seconds."""
        return self._timeout

    def set_timeout(self, value):
        """Set the update timer interval in seconds."""
        with self.restart_on_change(self.is_running()):
            self._timeout = value
            try:
                self._tmr.setInterval(int(self.get_timeout() * 1000))
            except (AttributeError, RuntimeError, Exception):
                pass

    def create_timer(self):
        """Actually create the timer."""
        # Check to run this function in the main thread.
        if threading.current_thread() != threading.main_thread():
            self.creating.emit()
            return

        self.stop(set_state=False)

        self._tmr = QtCore.QTimer()
        self._tmr.setSingleShot(False)
        self._tmr.setInterval(int(self.get_timeout() * 1000))
        self._tmr.timeout.connect(self.update)

    def is_running(self):
        """Return if running."""
        return self._running

    def stop(self, set_state=True):
        """Stop the updater timer."""
        # Check to run this function in the main thread.
        if threading.current_thread() != threading.main_thread():
            self.stopping.emit()
            return

        try:
            self._tmr.stop()
        except:
            pass
        if set_state:
            self._running = False

    def start(self):
        """Start the updater timer."""
        # Check to run this function in the main thread.
        if threading.current_thread() != threading.main_thread():
            self.starting.emit()
            return

        self.stop(set_state=False)
        self._running = True
        if self._tmr is None:
            self.create_timer()  # Should be in main thread
        self._tmr.start()

    def ensure_running(self):
        """If the updater is not running send a safe signal to start it."""
        if not self.is_running():
            self._running = True
            self.starting.emit()

    def register_continuous(self, func, *args, **kwargs):
        """Register a function to be called on every update continuously."""
        with self._always_lock:
            self._always_call[func] = (args, kwargs)
        self.ensure_running()

    def unregister_continuous(self, func):
        """Unregister a function to be called on every update continuously."""
        with self._always_lock:
            try:
                self._always_call.pop(func, None)
            except:
                pass

    def call_latest(self, func, *args, **kwargs):
        """Call the most recent values for this function in the main thread on the next update call."""
        with self._latest_lock:
            self._call_latest[func] = (args, kwargs)
        self.ensure_running()

    def now_call_latest(self, func, *args, **kwargs):
        """Call the latest value in the main thread. If this is the main thread call now."""
        if threading.current_thread() == threading.main_thread():
            func(*args, **kwargs)
        else:
            self.call_latest(func, *args, **kwargs)

    def call_in_main(self, func, *args, **kwargs):
        """Call this function in the main thread on the next update call."""
        with self._main_lock:
            try:
                self._call_in_main[func].append((args, kwargs))
            except (KeyError, IndexError, Exception):
                self._call_in_main[func] = [(args, kwargs)]
        self.ensure_running()

    def now_call_in_main(self, func, *args, **kwargs):
        """Call in the main thread. If this is the main thread call now."""
        if threading.current_thread() == threading.main_thread():
            func(*args, **kwargs)
        else:
            self.call_in_main(func, *args, **kwargs)

    def update(self):
        """Run the stored function calls to update the GUI items in the main thread.

        This function should not be called directly. Call `ThreadUpdater.start()` to run this function on a timer in
        the main thread.
        """
        with self._always_lock:
            always = self._always_call.copy()
        with self._latest_lock:
            latest, self._call_latest = self._call_latest, OrderedDict()
        with self._main_lock:
            main, self._call_in_main = self._call_in_main, OrderedDict()

        for func, (args, kwargs) in always.items():
            with self.handle_error(func):
                func(*args, **kwargs)

        for func, (args, kwargs) in latest.items():
            with self.handle_error(func):
                func(*args, **kwargs)

        for func, li in main.items():
            for args, kwargs in li:
                with self.handle_error(func):
                    func(*args, **kwargs)
