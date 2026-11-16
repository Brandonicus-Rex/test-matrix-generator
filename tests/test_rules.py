"""Tests for the rule language: parsing, validation and three-valued evaluation."""

import pytest

from matrixgen.rules import RuleError, compile_rule

DOMAINS = {
    "plan": ["basic", "plus", "unlimited"],
    "device": ["phone", "tablet", "iot"],
    "voicemail": ["on", "off"],
}


def rule(text):
    return compile_rule(text, DOMAINS)


@pytest.mark.parametrize("text,assignment,expected", [
    ("plan == 'basic'", {"plan": "basic"}, True),
    ("plan != basic", {"plan": "basic"}, False),            # bare-word values work too
    ("plan in ['plus', 'unlimited']", {"plan": "plus"}, True),
    ("plan not in [plus, unlimited]", {"plan": "plus"}, False),
    ("not device == iot", {"device": "phone"}, True),
    ("device == iot and voicemail == on", {"device": "iot", "voicemail": "off"}, False),
    ("device == iot or voicemail == on", {"device": "phone", "voicemail": "on"}, True),
    ("(device == iot or device == tablet) -> voicemail == off", {"device": "tablet", "voicemail": "on"}, False),
    ("device == iot -> voicemail == off", {"device": "phone", "voicemail": "on"}, True),
])
def test_evaluate_complete(text, assignment, expected):
    assert rule(text).evaluate(assignment) is expected


def test_implication_is_right_associative():
    # a -> (b -> c): false only when a and b are true and c is false
    r = rule("plan == basic -> device == iot -> voicemail == off")
    assert r.evaluate({"plan": "basic", "device": "iot", "voicemail": "on"}) is False
    assert r.evaluate({"plan": "plus", "device": "iot", "voicemail": "on"}) is True


def test_partial_assignments_are_three_valued():
    r = rule("device == iot -> voicemail == off")
    assert r.evaluate({}) is None                      # nothing known yet
    assert r.evaluate({"device": "phone"}) is True      # already satisfied
    assert r.evaluate({"device": "iot"}) is None        # depends on voicemail
    assert r.evaluate({"voicemail": "off"}) is True     # satisfied whatever the device
    assert r.evaluate({"device": "iot", "voicemail": "on"}) is False


def test_params_are_recorded():
    assert rule("device == iot -> voicemail == off").params == {"device", "voicemail"}


@pytest.mark.parametrize("text,message", [
    ("", "empty"),
    ("device == ", "expected word"),
    ("colour == red", "unknown parameter"),
    ("device == iott", "is not a value"),          # typos are caught, not silently ignored
    ("device iot", "expected ==, !=, in"),
    ("device == iot )", "unexpected"),
    ("and == iot", "parameter name"),
    ("device in iot", "expected lbr"),
    ("device == iot; import os", "unexpected character"),
    ("__import__('os').system('x') == 1", "expected =="),  # rejected at parse, never run
])
def test_bad_rules_are_rejected(text, message):
    with pytest.raises(RuleError, match=message):
        rule(text)
