import pytest

@pytest.mark.unit
def test_basic_math():
    """
    A simple test that doesn't depend on any external services.
    This is useful to verify that the test framework is working.
    """
    assert 1 + 1 == 2
    assert 2 * 2 == 4
    
@pytest.mark.unit
def test_string_operations():
    """
    Test basic string operations.
    """
    assert "hello" + " world" == "hello world"
    assert "EverRaise".lower() == "everraise"
    assert "ai analytics".title() == "Ai Analytics" 