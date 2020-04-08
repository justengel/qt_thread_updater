

def run_simple_thread_example():
    """Run the normal usage thread example."""
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


def run_continuous_update():
    """Run the continuous update example."""
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


def run_call_in_main():
    """Run the updater call_in_main. This will be inefficient and may need to run slower (time.sleep)."""
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


if __name__ == '__main__':
    from qt_thread_updater import cleanup_app

    run_simple_thread_example()
    cleanup_app()

    run_continuous_update()
    cleanup_app()

    run_call_in_main()
    cleanup_app()
