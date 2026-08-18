"""Tests for setup_logging.

The log directory is resolved against the current working directory, which is
the kind of thing that silently writes outside the project when it goes wrong,
so it is pinned down here.
"""

import logging
import subprocess
import sys
from pathlib import Path

import pytest

from ingestion_engine.config.log_config import LOG_FILE_NAME, setup_logging


@pytest.fixture(autouse=True)
def isolated_logging():
    """Restore the root logger, closing the handlers this test attached.

    Without closing them the rotating file handler keeps the log file open,
    which stops the temporary directory from being cleaned up on Windows.
    """

    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level

    root.handlers.clear()

    yield

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    root.handlers.extend(saved_handlers)
    root.setLevel(saved_level)


def test_the_log_directory_is_created(tmp_path: Path):
    setup_logging(log_dir=tmp_path / "logs")

    assert (tmp_path / "logs").is_dir()


def test_missing_parent_directories_are_created(tmp_path: Path):
    """A nested target must not fail with FileNotFoundError."""

    setup_logging(log_dir=tmp_path / "var" / "log" / "ingestion")

    assert (tmp_path / "var" / "log" / "ingestion").is_dir()


def test_calling_it_twice_is_harmless(tmp_path: Path):
    setup_logging(log_dir=tmp_path / "logs")
    setup_logging(log_dir=tmp_path / "logs")

    assert (tmp_path / "logs").is_dir()


def test_a_relative_directory_stays_inside_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The default must not resolve above the working directory."""

    monkeypatch.chdir(tmp_path)

    setup_logging()

    assert (tmp_path / "logs").is_dir()
    assert not (tmp_path.parent / "logs").exists()


def test_messages_are_written_to_the_log_file(tmp_path: Path):
    setup_logging(log_dir=tmp_path / "logs")

    logging.getLogger("test").info("a message worth keeping")

    for handler in logging.getLogger().handlers:
        handler.flush()

    assert "a message worth keeping" in (tmp_path / "logs" / LOG_FILE_NAME).read_text(
        encoding="utf-8"
    )


def test_the_level_is_applied(tmp_path: Path):
    setup_logging(level="WARNING", log_dir=tmp_path / "logs")

    logging.getLogger("test").info("should be filtered out")
    logging.getLogger("test").warning("should be kept")

    for handler in logging.getLogger().handlers:
        handler.flush()

    written = (tmp_path / "logs" / LOG_FILE_NAME).read_text(encoding="utf-8")

    assert "should be filtered out" not in written
    assert "should be kept" in written


def test_importing_the_module_creates_nothing(tmp_path: Path):
    """Configuring logging is an action, so importing must have no side effect."""

    subprocess.run(
        [sys.executable, "-c", "import ingestion_engine.config.log_config"],
        cwd=tmp_path,
        check=True,
    )

    assert list(tmp_path.iterdir()) == []
