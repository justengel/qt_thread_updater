"""
Thread Updater module to help update GUI items in a separate thread.
"""
from .__meta__ import version as __version__

from qt_thread_updater.thread_updater import is_main_thread, ThreadUpdater
from qt_thread_updater.global_utils import get_updater, set_updater, cleanup_app,\
    get_global_updater_mngr, set_global_updater_mngr, GlobalUpdaterManager


__all__ = ['get_updater', 'set_updater', 'cleanup_app', 'ThreadUpdater', 'is_main_thread',
           'get_global_updater_mngr', 'set_global_updater_mngr', 'GlobalUpdaterManager']
