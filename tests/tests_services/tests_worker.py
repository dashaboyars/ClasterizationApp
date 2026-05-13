import pytest
from unittest.mock import MagicMock
from workers.import_thread import BackgroundThread

def test_background_thread_success(qtbot):
    def task(progress_callback, cancel_check):
        progress_callback(50, "Step 1")
        return "OK"
    thread = BackgroundThread(task)
    with qtbot.waitSignal(thread.finished, timeout=1000) as blocker:
        thread.start()
    thread.wait()
    assert blocker.args[0] == "OK"

def test_background_thread_error(qtbot):
    def task(progress_callback, cancel_check):
        raise ValueError("Test error")
    thread = BackgroundThread(task)
    with qtbot.waitSignal(thread.error, timeout=1000) as blocker:
        thread.start()
    thread.wait()
    assert blocker.args[0] == "Test error"

def test_background_thread_cancel(qtbot):
    def task(progress_callback, cancel_check):
        for i in range(10):
            if cancel_check():
                return None
        return "Done"
    thread = BackgroundThread(task)
    thread.start()
    thread.cancel()
    with qtbot.waitSignal(thread.finished, timeout=500, raising=False) as blocker:
        pass
    assert not blocker.signal_triggered   # сигнал не должен быть испущен
    thread.wait()  # дожидаемся завершения потока

def test_background_thread_progress(qtbot):
    progress_calls = []
    def task(progress_callback, cancel_check):
        progress_callback(10, "Start")
        progress_callback(50, "Middle")
        progress_callback(100, "End")
        return "Result"
    thread = BackgroundThread(task)
    thread.progress.connect(lambda v, s: progress_calls.append((v, s)))
    with qtbot.waitSignal(thread.finished, timeout=1000):
        thread.start()
    thread.wait()
    assert progress_calls == [(10, "Start"), (50, "Middle"), (100, "End")]