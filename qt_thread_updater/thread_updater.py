"""
Thread Updater module to help update GUI items in a separate thread.
"""
import sys
import time
import threading
import traceback
import contextlib
from collections import OrderedDict

from qtpy import QtCore, QtWidgets


__all__ = ['is_main_thread', 'ThreadUpdater']


def is_main_thread():
    """Return if the current thread is the main thread."""
    return threading.current_thread() is threading.main_thread()


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

    class DebugTypes:
        PRINT_ERROR = 'print'  # Print to stderr
        HIDE_ERROR = 'hide'    # Do nothing and hide the error
        RAISE_ERROR = 'raise'  # Crash the update function and raise the error

    PRINT_ERROR = DebugTypes.PRINT_ERROR
    HIDE_ERROR = DebugTypes.HIDE_ERROR
    RAISE_ERROR = DebugTypes.RAISE_ERROR

    DEFAULT_DEBUG_TYPE = PRINT_ERROR

    def __init__(self, timeout=1/30, debug_type=None, parent=None, init_later=False, **kwargs):
        """Initialize the ThreadUpdater.

        Args:
             timeout (float/int)[1/30]: Interval in which to run the update functions (in seconds).
             debug_type (str)[DEFAULT_DEBUG_TYPE]: Control to manage how errors are handled.
             parent (QtCore.QObject)[None]: Parent QObject.
             init_later (bool)[False]: Manually initialize this object later with `init()`.
        """
        super().__init__(parent)

        if debug_type is None:
            debug_type = self.DEFAULT_DEBUG_TYPE

        # Lock and update variables
        self._latest_call = OrderedDict()
        self._latest_lock = threading.RLock()
        self._every_call = OrderedDict()
        self._every_lock = threading.RLock()
        self._always_call = OrderedDict()
        self._always_lock = threading.RLock()
        self._delay_call = []
        self._delay_lock = threading.RLock()

        # Control variables
        self._timeout = timeout
        self.debug_type = debug_type
        self._running = False
        self._tmr = None

        # Try to initialize later so thread variables can be set as fast as possible.
        if not init_later:
            self.init()

    def init(self, *args, **kwargs):
        """Initialize here; Try to make creating the object in __init__ as fast as possible and with little complexity.

        This is to
        reduce the chance that two threads create the global MAIN_UPDATER at the same time. Yes, I've seen this and it
        was problematic.
        """
        # Move to main thread before connecting the signals, so signals run in the main thread
        if not is_main_thread():
            self.moveToThread(QtWidgets.QApplication.instance().thread())

        # Connect the signals
        self.starting.connect(self.start)
        self.stopping.connect(self.stop)
        self.creating.connect(self.create_timer)

        # Create the timer
        self.create_timer()
        return self

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
        if not is_main_thread():
            self.creating.emit()
            return

        self.stop(set_state=False)

        self._tmr = QtCore.QTimer()
        self._tmr.setSingleShot(False)
        self._tmr.setInterval(int(self.get_timeout() * 1000))
        self._tmr.timeout.connect(self.run_update)

    def is_running(self):
        """Return if running."""
        return self._running

    def stop(self, set_state=True):
        """Stop the updater timer."""
        # Check to run this function in the main thread.
        if not is_main_thread():
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
        if not is_main_thread():
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
            self._latest_call[func] = (args, kwargs)
        self.ensure_running()

    def now_call_latest(self, func, *args, **kwargs):
        """Call the latest value in the main thread. If this is the main thread call now."""
        if is_main_thread():
            func(*args, **kwargs)
        else:
            self.call_latest(func, *args, **kwargs)

    def call_in_main(self, func, *args, **kwargs):
        """Call this function in the main thread on the next update call."""
        with self._every_lock:
            try:
                self._every_call[func].append((args, kwargs))
            except (KeyError, IndexError, Exception):
                self._every_call[func] = [(args, kwargs)]
        self.ensure_running()

    def now_call_in_main(self, func, *args, **kwargs):
        """Call in the main thread. If this is the main thread call now."""
        if is_main_thread():
            func(*args, **kwargs)
        else:
            self.call_in_main(func, *args, **kwargs)

    def delay(self, seconds, func, *args, **kwargs):
        """Call the given function after the given number of seconds has passed.

        This will not be accurate unless your timeout is at a high rate (lower timeout number).

        Args:
            seconds (float/int): Number of seconds to wait until calling the function.
            func (callable): Function to call.
            *args (tuple): Positional arguments to pass into the function.
            **kwargs (dict): Keyword arguments to pass into the function.
        """
        now = time.time()  # Note: this is before the lock
        with self._delay_lock:
            self._delay_call.append(DelayedFunc(now, seconds, func, args, kwargs))
        self.ensure_running()

    def run_update(self):
        """Run the stored function calls to update the GUI items in the main thread.

        This function should not be called directly. Call `ThreadUpdater.start()` to run this function on a timer in
        the main thread.
        """
        # Collect the items using the thread safe lock
        with self._always_lock:
            always = self._always_call.copy()
        with self._latest_lock:
            latest, self._latest_call = self._latest_call, OrderedDict()
        with self._every_lock:
            main, self._every_call = self._every_call, OrderedDict()
        with self._delay_lock:
            delayed = [self._delay_call.pop(i) for i in reversed(range(len(self._delay_call)))
                       if self._delay_call[i].can_run()]

        # Start running the functions
        for delayed_func in delayed:
            with self.handle_error(delayed_func.func):
                delayed_func.func(*delayed_func.args, **delayed_func.kwargs)

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


class DelayedFunc(object):
    def __init__(self, start_time, delay_time, func, args, kwargs):
        self.start_time = start_time
        self.delay_time = delay_time
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def can_run(self):
        """Return if the time to wait is over."""
        return (time.time() - self.start_time) >= self.delay_time

    def wait_for(self, from_time=None):
        """Return the number of seconds from now until this function should run."""
        if from_time is None:
            from_time = time.time()
        wait = (self.start_time + self.delay_time) - from_time
        if wait < 0:
            wait = 0
        return wait
