# tests/test_generate_onyx_samplesheet.py
# Import the module under test
# Adjust the import path to match your package layout, e.g.:
# from gpha_mscape_nf_amr.generate_onyx_samplesheet import get_args, get_record, main, config
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

MODULE_IMPORT_PATH = "gpha_mscape_nf_amr.generate_onyx_samplesheet"
mod = importlib.import_module(MODULE_IMPORT_PATH)


# ---------- Utilities ----------


class NoOpDecorator:
    """A simple stand-in for @oa.call_to_onyx so the function runs as-is."""

    def __call__(self, func):
        return func


@pytest.fixture(autouse=True)
def no_op_oa_decorator(monkeypatch):
    """
    Replace oa.call_to_onyx decorator with a no-op so that tests don't rely on
    external behavior/logging/retries etc. We only care about our function logic.
    """
    # Patch the attribute on the already-imported module
    monkeypatch.setattr(mod.oa, "call_to_onyx", NoOpDecorator(), raising=True)


@pytest.fixture
def fake_env(monkeypatch):
    """
    Provide the env vars expected by OnyxConfig at import time.
    If your module creates `config = OnyxConfig(...)` at import,
    we need those envs set before any code uses `config`.
    """
    # The keys are accessed via OnyxEnv.DOMAIN and OnyxEnv.TOKEN
    monkeypatch.setenv(mod.OnyxEnv.DOMAIN, "example.org")
    monkeypatch.setenv(mod.OnyxEnv.TOKEN, "dummy-token")


# ---------- Tests for get_args ----------
def test_get_args_parses_required_flags(monkeypatch, tmp_path):
    out = tmp_path / "out.csv"
    argv = [
        "prog",
        "-i",
        "SAMPLE123",
        "-c",
        "col1,col2",
        "-o",
        str(out),
    ]
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    monkeypatch.setattr(sys, "argv", argv)

    args = mod.get_args()
    assert args.id == "SAMPLE123"
    assert args.columns == "col1,col2"
    assert isinstance(args.output, Path)
    assert args.output == out


def test_get_args_requires_flags(monkeypatch):
    # Missing required flags should cause SystemExit from argparse
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(SystemExit):
        _ = mod.get_args()


# ---------- Tests for get_record ----------


def test_get_record_appends_climb_id_and_calls_onyx(fake_env, monkeypatch):
    # Prepare a fake client with a .filter method that returns rows
    # The code under test does: pd.DataFrame(client.filter(...))
    fake_rows = [{"climb_id": "S1", "col1": "A", "col2": "B"}]

    # The OnyxClient is used as a context manager
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.__exit__.return_value = False
    fake_client.filter.return_value = fake_rows

    # Patch OnyxClient in the module under test
    monkeypatch.setattr(mod, "OnyxClient", MagicMock(return_value=fake_client))

    # Start with no "climb_id" in the request columns
    cols = ["col1", "col2"]
    df, exit_code = mod.get_record("S1", cols)

    # The function should have appended "climb_id"
    assert "climb_id" in cols

    # It should have constructed a DataFrame from the returned rows
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["climb_id", "col1", "col2"]
    assert len(df) == 1
    assert exit_code == 0

    # Verify the filter call arguments
    fake_client.filter.assert_called_once_with(
        project="mscape",
        climb_id="S1",
        include=["col1", "col2", "climb_id"],
    )


def test_get_record_keeps_existing_climb_id(fake_env, monkeypatch):
    fake_rows = [{"climb_id": "S2", "colX": 42}]
    fake_client = MagicMock()
    fake_client.__enter__.return_value = fake_client
    fake_client.filter.return_value = fake_rows
    monkeypatch.setattr(mod, "OnyxClient", MagicMock(return_value=fake_client))

    cols = ["climb_id", "colX"]
    df, code = mod.get_record("S2", cols)

    # Should not duplicate climb_id
    assert cols.count("climb_id") == 1
    assert set(df.columns) == {"climb_id", "colX"}
    assert code == 0


# ---------- Tests for main (integration-ish) ----------


def test_main_writes_csv(tmp_path, fake_env, monkeypatch):
    """
    Patch get_record to return a known DataFrame and ensure main writes it to CSV.
    We also patch argv for get_args.
    """
    out = tmp_path / "result.csv"
    argv = [
        "prog",
        "-i",
        "SAMPLE9",
        "-c",
        "a,b",
        "-o",
        str(out),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    # Fake DF result from get_record
    df = pd.DataFrame([{"climb_id": "SAMPLE9", "a": 1, "b": 2}])

    # Patch get_record to avoid hitting Onyx in this test
    monkeypatch.setattr(mod, "get_record", MagicMock(return_value=(df, 0)))

    # Run main
    mod.main()

    # Assert the file exists and content looks right
    assert out.exists()
    loaded = pd.read_csv(out)
    assert list(loaded.columns) == ["climb_id", "a", "b"]
    assert loaded.iloc[0].to_dict() == {"climb_id": "SAMPLE9", "a": 1, "b": 2}
