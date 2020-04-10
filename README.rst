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

  * delay - Call a function after the given number of seconds has passed.

    * This will not be accurate. Accuracy can be improved by lowering the timeout to increase how often the timer runs.

ThreadUpdater Examples
======================

Below are some examples of how the ThreadUpdater would normally be used.

Simple Thread Example
~~~~~~~~~~~~~~~~~~~~~

The example below tells the update to run lbl.setText in the main thread with the latest value.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    lbl = QtWidgets.QLabel("Latest Count: 0")
    lbl.resize(300, 300)
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
~~~~~~~~~~~~~~~~~~~~~~~~~

The example below continuously runs the update function every time `ThreadUpdater.update()` is called from the timer.
This may be inefficient if there is no new data to update the label with.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    lbl = QtWidgets.QLabel("Continuous Count: 0")
    lbl.resize(300, 300)
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
~~~~~~~~~~~~~~~~~~~~

The example below calls the append function every time. It may not be efficient.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QtWidgets.QTextEdit()
    text_edit.resize(300, 300)
    text_edit.setReadOnly(True)
    text_edit.show()

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            text = 'Main Count: {}'.format(data['counter'])
            get_updater().call_in_main(text_edit.append, text)
            data['counter'] += 1
            time.sleep(0.01)  # Some delay/waiting is required

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()


Delay Example
~~~~~~~~~~~~~

The example below calls the append function after X number of seconds has passed. The delay function will not be
accurate, but guarantees that the function is called after X number of seconds. To increase accuracy give the
`ThreadUpdater` a smaller timeout for it to run at a faster rate.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QtWidgets.QTextEdit()
    text_edit.resize(300, 300)
    text_edit.setReadOnly(True)
    text_edit.show()

    now = time.time()

    def update_text(set_time):
        text_edit.append('Requested {:.04f} Updated {:.04f}'.format(set_time, time.time() - now))

    # Lower the timeout so it runs at a faster rate.
    get_updater().timeout = 0  # 0.0001  # Qt runs in milliseconds

    get_updater().delay(0.5, update_text, 0.5)
    get_updater().delay(1, update_text, 1)
    get_updater().delay(1.5, update_text, 1.5)
    get_updater().delay(2, update_text, 2)
    get_updater().delay(2.5, update_text, 2.5)
    get_updater().delay(3, update_text, 3)

    app.exec_()


Widgets
=======

I've decdied to include a couple of useful Qt Widgets with this library.

  * QuickPlainTextEdit - Used to display fast streams of data
  * QuickTextEdit - Display fast streams of data with color.


QuickPlainTextEdit
~~~~~~~~~~~~~~~~~~

Quickly display data from a separate thread.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater.widgets.quick_text_edit import QuickPlainTextEdit

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QuickPlainTextEdit()
    text_edit.resize(300, 300)
    text_edit.show()

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            text = 'Main Count: {}\n'.format(data['counter'])
            text_edit.write(text)
            data['counter'] += 1
            time.sleep(0.0001)  # Some delay is usually required to let the Qt event loop run (not needed if IO used)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()


QuickTextEdit
~~~~~~~~~~~~~

Quickly display data from a separate thread using color.

.. code-block:: python

    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater.widgets.quick_text_edit import QuickTextEdit

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QuickTextEdit()
    text_edit.resize(300, 300)
    text_edit.show()

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            text = 'Main Count: {}\n'.format(data['counter'])
            text_edit.write(text, 'blue')
            data['counter'] += 1
            time.sleep(0.0001)  # Some delay is usually required to let the Qt event loop run (not needed if IO used)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()

QuickTextEdit Redirect
~~~~~~~~~~~~~~~~~~~~~~

Display print (stdout and stderr) in a QTextEdit with color.

.. code-block:: python

    import sys
    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater.widgets.quick_text_edit import QuickTextEdit

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QuickTextEdit()
    text_edit.resize(300, 300)
    text_edit.show()

    sys.stdout = text_edit.redirect(color='blue', iostream=sys.__stdout__)
    sys.stderr = text_edit.redirect(color='red', iostream=sys.__stderr__)

    data = {'counter': 0}

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            stdout_text = 'Main Count: {}'.format(data['counter'])  # Print gives \n automatically
            error_text = 'Error Count: {}'.format(data['counter'])  # Print gives \n automatically

            # Print automatically give '\n' with the "end" keyword argument.
            print(stdout_text)  # Print will write to sys.stdout where the rediect will write to text_edit and stdout
            print(error_text, file=sys.stderr)  # Print to sys.stderr. Rediect will write to text_edit and stderr

            data['counter'] += 1

            # Some delay is usually desired. print/sys.__stdout__ uses IO which gives time for Qt's event loop.
            # time.sleep(0.0001)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    app.exec_()
    alive.clear()
