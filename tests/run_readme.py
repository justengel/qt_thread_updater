from qt_thread_updater import cleanup_app


def run_simple_thread_example():
    """Run the normal usage thread example."""
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

    get_updater().delay(5, app.quit)  # Quit after 5 seconds
    app.exec_()
    alive.clear()
    cleanup_app()


def run_continuous_update():
    """Run the continuous update example that uses the global functions."""
    import time
    import threading
    from qtpy import QtWidgets
    import qt_thread_updater
    # from qt_thread_updater import get_updater

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    lbl = QtWidgets.QLabel("Continuous Count: 0")
    lbl.resize(300, 300)
    lbl.show()

    data = {'counter': 0}

    qt_thread_updater.set_updater(qt_thread_updater.ThreadUpdater(1/60))

    @qt_thread_updater.register_continuous
    def update():
        """Update the label with the current value."""
        lbl.setText('Continuous Count: {}'.format(data['counter']))

    # get_updater().register_continuous(update)

    def run(is_alive):
        is_alive.set()
        while is_alive.is_set():
            data['counter'] += 1
            # time.sleep(0.001)  # Not needed (still good to have some delay to release the thread)

    alive = threading.Event()
    th = threading.Thread(target=run, args=(alive,))
    th.start()

    qt_thread_updater.delay(5, app.quit)  # Quit after 5 seconds
    app.exec_()
    alive.clear()
    cleanup_app()


def run_call_in_main():
    """Run the updater call_in_main. This will be inefficient and may need to run slower (time.sleep)."""
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

    # Quit after 2 seconds (So many events from call in main 2 waits longer than 2 seconds)
    get_updater().delay(2, app.quit)
    app.exec_()
    alive.clear()
    cleanup_app()


def run_delay():
    """Run the updater to call a function delayed."""
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

    get_updater().delay(5, app.quit)  # Quit after 5 seconds
    app.exec_()
    cleanup_app()


if __name__ == '__main__':
    run_simple_thread_example()
    run_continuous_update()
    run_call_in_main()
    run_delay()
