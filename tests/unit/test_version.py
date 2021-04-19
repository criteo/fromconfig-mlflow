"""Test version."""

from fromconfig_mlflow import version


def test_version():
    """Test version."""
    assert len(version.__version__.split(".")) == 3
    assert isinstance(version.__author__, str)
