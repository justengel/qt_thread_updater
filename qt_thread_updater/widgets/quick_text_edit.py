import inspect
import threading
from collections import deque
from qtpy import QtWidgets, QtGui, QtCore
from qt_thread_updater import is_main_thread, get_updater


__all__ = ['clipboard', 'QuickPlainTextEdit', 'QuickTextEdit', 'StreamWrite']


def clipboard(text=None):
    """Return the clipboard text or set the clipboard text if text was given."""
    app = QtWidgets.QApplication.instance()

    if text is None:
        return app.clipboard().text()
    else:
        app.clipboard().setText(text)


class QuickPlainTextEdit(QtWidgets.QPlainTextEdit):
    """QuickPlainTextEdit allows you to quickly write text in a separate thread."""

    DEFAULT_MAX_BLOCKS = 800

    def __init__(self, *args, **kwargs):
        super(QuickPlainTextEdit, self).__init__(*args, **kwargs)

        self._queue_lock = threading.RLock()
        self._queue = deque()

        vert_bar = self.verticalScrollBar()
        self._last_scroll_range = (vert_bar.minimum(), vert_bar.maximum())
        vert_bar.rangeChanged.connect(self._check_scrollToBottom)

        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_context_menu)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard |
                                     QtCore.Qt.TextSelectableByMouse)

        self.setMaximumBlockCount(self.DEFAULT_MAX_BLOCKS)

    def custom_context_menu(self, position):
        """Create the standard context menu for the QTextEdit."""
        menu = self.createStandardContextMenu()

        # Clear
        clear_action = QtWidgets.QAction("Clear", None)
        clear_action.setToolTip("Clear the monitor text.")
        clear_action.triggered.connect(self.clear)
        menu.insertAction(menu.actions()[0], clear_action)

        # Copy all
        copy_all_action = menu.addAction("Copy All")
        # copy_all_action = QtGui.QAction(, None)
        copy_all_action.setToolTip("Copy all of the text in the monitor to the clipboard.")
        copy_all_action.triggered.connect(self.copy_all)
        # menu.addAction(copy_all_action)

        if self.document().isEmpty():
            clear_action.setEnabled(False)
            copy_all_action.setEnabled(False)

        menu.popup(self.mapToGlobal(position))
        return menu
    # end customContextMenu

    def copy_all(self):
        """Copy all of the text in the monitor to the clipboard."""
        clipboard(self.toPlainText())

    def setMaximumBlockCount(self, maximum):
        """Set the maximum number of blocks."""
        with self._queue_lock:
            if maximum <= 0:
                maximum = 0
            self._queue = deque(self._queue, maxlen=maximum)
        super().setMaximumBlockCount(maximum)

    def redirect(self, *iostreams, color=None, fmt=None, **kwargs):
        """Return an object which writes to this text edit with the given color (if supported).

        This is useful for replacing sys.stdout

        ..code-block::python

            widg = QuickTextEdit()
            sys.stderr.write = widg.redirect('red')

        Args:
            *iostreams (object)[None]: Additional object to write to.
            color (str/QColor)[None]: String color name to write the text foreground with.
                If this argument is None the currentCharFormat() or given fmt will be used.
            fmt (QTextCharFormat)[None]: Use this text format to write the text.

        Returns:
            redirect (RedirectStream): Callable write object to change the stdout.write to write to this object.
        """
        return StreamWrite(self, *iostreams, color=color, fmt=fmt, **kwargs)

    def write(self, text, *args, **kwargs):
        """Put data on the queue to add to the TextEdit view."""
        text = str(text)
        if len(text) > 0:
            with self._queue_lock:
                self._queue += text
            get_updater().call_latest(self.update_display)

    def update_display(self):
        """Update the display by taking data off of the queue and displaying it in the widget."""
        with self._queue_lock:
            text = ''.join((self._queue.popleft() for _ in range(len(self._queue))))

        if len(text) == 0:
            return

        cursor = QtGui.QTextCursor(self.textCursor())
        cursor.beginEditBlock()

        # Move and check the position
        # old_pos = cursor.position()
        cursor.movePosition(QtGui.QTextCursor.End)
        # is_end = cursor.position() == old_pos

        # Insert the text (This will insert text even without setTextCursor)
        cursor.insertText(text)
        cursor.endEditBlock()

    def _check_scrollToBottom(self, minv, maxv):
        """When the range changes check if it is larger than the last range and scroll to bottom if it is."""
        if maxv > self._last_scroll_range[1]:
            self._last_scroll_range = (minv, maxv)
            self.scrollToBottom()

    def scrollToBottom(self, *args, **kwargs):
        """Scroll the vertical scroll bar to the maximum position."""
        vert_bar = self.verticalScrollBar()
        vert_bar.setSliderPosition(vert_bar.maximum())


class QuickTextEdit(QtWidgets.QTextEdit):
    """Quick TextEdit for monitoring I/O.

    This works as a redirect for the output stream.

    ..code-block:: python

        import sys
        widg = QuickTextEdit()
        sys.stdout.write = widg.redirect('blue')
        sys.stderr.write = widg.redirect('red')
    """

    DEFAULT_MAX_BLOCKS = 800

    def __init__(self, *args, **kwargs):
        super(QuickTextEdit, self).__init__(*args, **kwargs)

        self._queue_lock = threading.RLock()
        self._queue = deque()
        self._orig_fmt = None

        vert_bar = self.verticalScrollBar()
        self._last_scroll_range = (vert_bar.minimum(), vert_bar.maximum())
        vert_bar.rangeChanged.connect(self._check_scrollToBottom)

        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_context_menu)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard |
                                     QtCore.Qt.TextSelectableByMouse)

        self.setMaximumBlockCount(self.DEFAULT_MAX_BLOCKS)

    def custom_context_menu(self, position):
        """Create the standard context menu for the QTextEdit."""
        menu = self.createStandardContextMenu()

        # Clear
        clear_action = QtWidgets.QAction("Clear", None)
        clear_action.setToolTip("Clear the monitor text.")
        clear_action.triggered.connect(self.clear)
        menu.insertAction(menu.actions()[0], clear_action)

        # Copy all
        copy_all_action = menu.addAction("Copy All")
        # copy_all_action = QtGui.QAction(, None)
        copy_all_action.setToolTip("Copy all of the text in the monitor to the clipboard.")
        copy_all_action.triggered.connect(self.copy_all)
        # menu.addAction(copy_all_action)

        if self.document().isEmpty():
            clear_action.setEnabled(False)
            copy_all_action.setEnabled(False)

        menu.popup(self.mapToGlobal(position))
        return menu

    def copy_all(self):
        """Copy all of the text in the monitor to the clipboard."""
        clipboard(self.toPlainText())

    def setMaximumBlockCount(self, maximum):
        """Set the maximum number of blocks."""
        with self._queue_lock:
            if maximum <= 0:
                maximum = 0
            self._queue = deque(self._queue, maxlen=maximum)
        self.document().setMaximumBlockCount(maximum)

    def redirect(self, *iostreams, color=None, fmt=None, **kwargs):
        """Return an object which writes to this text edit with the given color (if supported).

        This is useful for replacing sys.stdout

        ..code-block::python

            widg = QuickTextEdit()
            sys.stderr.write = widg.redirect('red')

        Args:
            *iostreams (object)[None]: Additional object to write to.
            color (str/QColor)[None]: String color name to write the text foreground with.
                If this argument is None the currentCharFormat() or given fmt will be used.
            fmt (QTextCharFormat)[None]: Use this text format to write the text.

        Returns:
            redirect (RedirectStream): Callable write object to change the stdout.write to write to this object.
        """
        return StreamWrite(self, *iostreams, color=color, fmt=fmt, **kwargs)

    def write(self, text, color=None, fmt=None, *args, **kwargs):
        """Put data on the queue to add to the TextEdit view.

        Args:
            text (str): String text to write.
            color (str/QColor)[None]: String color name to write the text foreground with.
                If this argument is None the currentCharFormat() or given fmt will be used.
            fmt (QTextCharFormat)[None]: Use this text format to write the text.
        """
        text = str(text)
        if len(text) > 0:
            # Get and copy the format. Do not permanently change the format
            if fmt is None:
                fmt = self._orig_fmt or self.currentCharFormat()
            fmt = QtGui.QTextCharFormat(fmt)

            # Change the color
            if color is not None:
                fmt.setForeground(QtGui.QBrush(QtGui.QColor(color)))

            with self._queue_lock:
                self._queue.append((text, fmt))

            get_updater().call_latest(self.update_display)

    def update_display(self):
        """Update the display by taking data off of the queue and displaying it in the widget."""
        with self._queue_lock:
            items = tuple(self._queue.popleft() for _ in range(len(self._queue)))

        if len(items) == 0:
            return

        self._orig_fmt = QtGui.QTextCharFormat(self.currentCharFormat())
        cursor = QtGui.QTextCursor(self.textCursor())
        cursor.beginEditBlock()

        # Move and check the position
        # old_pos = cursor.position()
        cursor.movePosition(QtGui.QTextCursor.End)
        # is_end = cursor.position() == old_pos

        # Insert the text
        for text, fmt in items:
            # cursor.setCharFormat(fmt)
            cursor.insertText(text, fmt)

        # End edit
        cursor.endEditBlock()
        self.setCurrentCharFormat(self._orig_fmt)
        self._orig_fmt = None

    def _check_scrollToBottom(self, minv, maxv):
        """When the range changes check if it is larger than the last range and scroll to bottom if it is."""
        if maxv > self._last_scroll_range[1]:
            self._last_scroll_range = (minv, maxv)
            self.scrollToBottom()

    def scrollToBottom(self, *args, **kwargs):
        """Scroll the vertical scroll bar to the maximum position."""
        vert_bar = self.verticalScrollBar()
        vert_bar.setSliderPosition(vert_bar.maximum())


class StreamWrite(object):
    """Custom object to overwrite a stream's write function. This could also be used as an io stream.

    Args:
        *iostreams (tuple/io.StringIO): Any number of io streams to write to.
        color (str/QColor)[None]: String color name to write the text foreground with.
            If this argument is None the currentCharFormat() or given fmt will be used.
        fmt (QTextCharFormat)[None]: Use this text format to write the text.
    """

    def __init__(self, *iostreams, color=None, fmt=None, **kwargs):
        self.iostreams = [stream for stream in iostreams]
        self.color = color
        self.fmt = fmt

    def add_stream(self, stream):
        """Add a stream to write to."""
        self.iostreams.append(stream)

    def remove_stream(self, stream):
        """Remove a stream."""
        try:
            self.iostreams.remove(stream)
        except:
            pass

    def write(self, text, color=None, fmt=None, **kwargs):
        """Write the text to all of the streams.

        This function does not indicate when an error occurs. This function passes kwargs into each stream.write().

        Args:
            text (str): String text to write.
            color (str/QColor)[None]: String color name to write the text foreground with.
                If None the set instance value is used. If the set argument is None the currentCharFormat() or given
                fmt will be used.
            fmt (QTextCharFormat)[None]: Use this text format to write the text.
                If None the set instance value is used.
        """
        if fmt is None:
            fmt = self.fmt
        if not isinstance(color, (str, QtGui.QColor)):
            color = self.color
        if isinstance(color, QtGui.QColor):
            color = str(color.name())

        for stream in self.iostreams:
            try:
                sig = inspect.signature(stream.write)
                if 'color' in sig.parameters:
                    stream.write(text, color=color, fmt=fmt, **kwargs)
                else:
                    stream.write(text, **kwargs)
            except (AttributeError, TypeError, ValueError, Exception):
                pass

    def fileno(self):
        """Return the file handler identifier."""
        for stream in self.iostreams:
            try:
                return stream.fileno()
            except (AttributeError, Exception):
                pass
        return -1

    def flush(self):
        """Flush the iostream."""
        for stream in self.iostreams:
            try:
                return stream.flush()
            except (AttributeError, Exception):
                pass

    __call__ = write
