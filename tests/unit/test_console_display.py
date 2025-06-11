import pytest
from types import SimpleNamespace
from anonyfiles_cli.ui.console_display import ConsoleDisplay
from anonyfiles_cli.exceptions import ConfigurationError, FileIOError, ProcessingError


class DummyLogger:
    @staticmethod
    def log_error(context, exc):
        pass


def _capture_output(display, func, *args):
    display.console = display.console.__class__(record=True)
    with pytest.MonkeyPatch.context() as mp:
        from anonyfiles_cli import cli_logger
        mp.setattr(cli_logger, "CLIUsageLogger", DummyLogger)
        func(*args)
        return display.console.export_text()


def test_handle_error_configuration():
    display = ConsoleDisplay()
    msg = _capture_output(display, display.handle_error, ConfigurationError("bad"), "ctx")
    assert "configuration".lower() in msg.lower()


def test_handle_error_fileio():
    display = ConsoleDisplay()
    msg = _capture_output(display, display.handle_error, FileIOError("io"), "ctx")
    assert "fichier" in msg.lower()


def test_handle_error_processing():
    display = ConsoleDisplay()
    msg = _capture_output(display, display.handle_error, ProcessingError("proc"), "ctx")
    assert "traitement" in msg.lower()

