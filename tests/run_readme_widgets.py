from qt_thread_updater import cleanup_app


def run_quickplaintextedit():
    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater.widgets import QuickPlainTextEdit

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
    cleanup_app()  # Delete the QApplication so a new one can be created and run


def run_quicktextedit():
    import time
    import threading
    from qtpy import QtWidgets, QtGui
    from qt_thread_updater.widgets import QuickTextEdit

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QuickTextEdit()
    text_edit.setTextBackgroundColor(QtGui.QColor(124, 124, 134))
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
    cleanup_app()  # Delete the QApplication so a new one can be created and run


def run_quicktextedit_redirect():
    import sys
    import time
    import threading
    from qtpy import QtWidgets
    from qt_thread_updater.widgets import QuickTextEdit

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    text_edit = QuickTextEdit()
    text_edit.resize(300, 300)
    text_edit.show()

    sys.stdout = text_edit.redirect(sys.__stdout__, color='blue')
    sys.stderr = text_edit.redirect(sys.__stderr__, color='red')

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
    cleanup_app()  # Delete the QApplication so a new one can be created and run


if __name__ == '__main__':
    # run_quickplaintextedit()
    run_quicktextedit()
    run_quicktextedit_redirect()
