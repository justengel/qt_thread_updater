=================
Qt Thread Updater
=================

Python Qt thread updater to update GUI items using a separate thread.

This library allows you to efficiently update Qt GUI elements from a separate thread. Qt GUI elements are not thread
safe. Method calls like `Label.setText` do not work in a separate thread. This library solves that problem.


Utilities
=========

The ThreadUpdater offers several utilities to help with updating a widget's value.

  * call_latest - Call the given function with the most recent value in the main thread using the timer.

    * It is safe to call this many times with the same function.
    * If the given function is called multiple times it is only called once with the most recent value.

  * call_in_main - Call the given function in the main thread using the timer.

    * Every time you call this function the given function will be called in the main thread
    * If the given function is called multiple times it will be called every time in the main thread.
    * If this function is called too many times it could slow down the main event loop.

  * register_continuous - Register a function to be called every time the `ThreadUpdater.update` method is called.

    * The `timeout` variable (in seconds) indicates how often the registered functions will be called.


Simple Thread Example
=====================

The example below tells the update to run lbl.setText in the main thread with the latest value.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    lbl = QtWidgets.QLabel("Latest Count: 0")
    lbl.resize(200, 200)
    lbl.show()

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            text = 'Latest Count: {}'.format(data['counter'])
            get_updater().call_latest(lbl.setText, text)
            data['counter'] += 1
            time.sleep(0.001)  # Not needed (still good to have some delay to release the thread)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()


Continuous Update Example
=========================

The example below continuously runs the update function every time `ThreadUpdater.update()` is called from the timer.
This may be inefficient if there is no new data to update the label with.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    lbl = QtWidgets.QLabel("Continuous Count: 0")
    lbl.resize(200, 200)
    lbl.show()

    data = {'counter': 0}

    def update():
        """Update the label with the current value."""
        lbl.setText('Continuous Count: {}'.format(data['counter']))

    get_updater().register_continuous(update)

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            data['counter'] += 1
            # time.sleep(0.001)  # Not needed (still good to have some delay to release the thread)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()


Call In Main Example
====================

The example below calls the append function every time. It may not be efficient.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QtWidgets.QTextEdit()
    text_edit.resize(200, 200)
    text_edit.setReadOnly(True)
    text_edit.show()

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            text = 'Main Count: {}'.format(data['counter'])
            get_updater().call_in_main(text_edit.append, text)
            data['counter'] += 1
            time.sleep(0.01)  # Some delay is required

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()
