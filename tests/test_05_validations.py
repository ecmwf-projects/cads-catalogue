import logging

from cads_catalogue import validations


def test_validate_stringchoicewidget(caplog) -> None:
    widget_data = {
        "name": "variable",
        "type": "StringChoiceWidget",
        "details": {
            "values": [
                "average_temperature",
                "maximum_temperature",
                "minimum_temperature",
            ],
        },
    }
    validations.validate_stringchoicewidget(widget_data)
    with caplog.at_level(logging.ERROR):
        log_msgs = [r.msg for r in caplog.records]
        assert (
            "found StringChoiceWidget named 'variable' without a default value"
            in log_msgs
        )
    caplog.clear()

    widget_data = {
        "name": "variable",
        "type": "StringChoiceWidget",
        "details": {
            "default": ["maximum_temperature"],
        },
    }
    validations.validate_stringchoicewidget(widget_data)
    with caplog.at_level(logging.ERROR):
        log_msgs = [r.msg for r in caplog.records]
        assert (
            "found StringChoiceWidget named 'variable' without a list of values"
            in log_msgs
        )
    caplog.clear()

    widget_data = {
        "name": "variable",
        "type": "StringChoiceWidget",
        "details": {
            "values": [
                "average_temperature",
                "maximum_temperature",
                "minimum_temperature",
            ],
            "default": ["new value"],
        },
    }
    validations.validate_stringchoicewidget(widget_data)
    with caplog.at_level(logging.ERROR):
        log_msgs = [r.msg for r in caplog.records]
        assert (
            "default of StringChoiceWidget named 'variable' is not included in the allowed list of values"
            in log_msgs
        )
    caplog.clear()

    widget_data = {
        "name": "variable",
        "type": "StringChoiceWidget",
        "details": {
            "values": [
                "average_temperature",
                "maximum_temperature",
                "minimum_temperature",
            ],
            "default": "maximum_temperature",
        },
    }
    validations.validate_stringchoicewidget(widget_data)
    with caplog.at_level(logging.ERROR):
        log_msgs = [r.msg for r in caplog.records]
        assert (
            "default of StringChoiceWidget named 'variable' must be defined as a list of one element"
            in log_msgs
        )
    caplog.clear()

    widget_data = {
        "name": "variable",
        "type": "StringChoiceWidget",
        "details": {
            "values": [
                "average_temperature",
                "maximum_temperature",
                "minimum_temperature",
            ],
            "default": ["maximum_temperature"],
        },
    }
    validations.validate_stringchoicewidget(widget_data)
    with caplog.at_level(logging.ERROR):
        log_msgs = [r.msg for r in caplog.records]
        assert not log_msgs
    caplog.clear()
