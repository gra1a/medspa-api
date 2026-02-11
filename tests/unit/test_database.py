"""Unit tests for app.db.database — transaction, get_db, create_all."""

from unittest.mock import MagicMock, patch

import pytest

from app.db.database import create_all, get_db, transaction

pytestmark = pytest.mark.unit


def test_transaction_commits_on_success():
    """When the with block completes, session.commit() is called."""
    session = MagicMock()
    with transaction(session):
        pass
    session.commit.assert_called_once()
    session.rollback.assert_not_called()


def test_transaction_rolls_back_and_reraises_on_exception():
    """When the with block raises, session.rollback() is called and the exception propagates."""
    session = MagicMock()
    with pytest.raises(ValueError, match="oops"):
        with transaction(session):
            raise ValueError("oops")
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_transaction_logs_on_rollback():
    """On exception, logger.exception is invoked."""
    session = MagicMock()
    with patch("app.db.database.logger") as mock_logger:
        with pytest.raises(RuntimeError):
            with transaction(session):
                raise RuntimeError("fail")
        mock_logger.exception.assert_called_once()
        assert "rollback" in mock_logger.exception.call_args[0][0].lower()


def test_get_db_yields_session_and_closes_on_exit():
    """get_db yields a session from SessionLocal and closes it in finally."""
    mock_session = MagicMock()
    with patch("app.db.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        session = next(gen)
        assert session is mock_session
        try:
            next(gen)
        except StopIteration:
            pass
    mock_session.close.assert_called_once()


def test_create_all_calls_metadata_create_all():
    """create_all() calls Base.metadata.create_all with the engine."""
    with patch("app.db.database.Base.metadata.create_all") as mock_create:
        from app.db import database

        create_all()
        mock_create.assert_called_once_with(bind=database.engine)
