import wx
import pytest


@pytest.fixture(scope="session")
def wx_app():
    """Create a single wx.App for all GUI-touching tests."""
    app = wx.App(redirect=False)
    yield app
    # let wx clean up; do not re-create another app in this process
