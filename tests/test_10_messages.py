
import datetime
import os.path

from cads_catalogue import messages

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_MESSAGE_ROOT_PATH = os.path.join(TESTDATA_PATH, "cads-messages")


def test_load_messages() -> None:
    msg_root = os.path.join(TESTDATA_PATH, "cads-messages")
    expected_msgs = [
        {
            "date": datetime.datetime(2023, 1, 13, 11, 27, 13),
            "entries": ["reanalisys-era5-land", "satellite-surface-xxx"],
            "live": False,
            "is_global": False,
            "message_body": "<h1>message main body for archived critical message for "
            "some datasets</h1>\n"
            "<p>Wider <strong>markdown syntax</strong> allowed here.</p>",
            "status": "ongoing",
            "severity": "critical",
            "summary": "example of expired critical content message",
        },
        {
            "date": datetime.datetime(2023, 1, 12, 11, 27, 13),
            "entries": ["reanalisys-era5-land", "satellite-surface-radiation-budget"],
            "live": True,
            "is_global": False,
            "message_body": "<h1>message main body for active critical message for some "
            "datasets</h1>\n"
            "<p>Wider <strong>markdown syntax</strong> allowed here.</p>",
            "status": "ongoing",
            "severity": "critical",
            "summary": "example of active critical content message",
        },
        {
            "date": datetime.datetime(2023, 1, 11, 11, 27, 13),
            "entries": ["reanalisys-era5-xxx", "satellite-surface-radiation-budget"],
            "live": False,
            "is_global": False,
            "message_body": "<h1>message main body for archived warning message for some "
            "entries</h1>\n"
            "<p>Wider <strong>markdown syntax</strong> allowed here. In "
            "this example:\n"
            "* <em>summary</em> is missing, so only this main body "
            "message is used\n"
            "* <em>status</em> is missing (indeed actually is not used "
            "yet)</p>",
            "status": "ongoing",
            "severity": "warning",
            "summary": "",
        },
        {
            "date": datetime.datetime(2021, 1, 14, 11, 27, 13),
            "entries": [""],
            "live": True,
            "is_global": True,
            "message_body": "<h1>main message content</h1>\n"
            "<p>Wider <strong>markdown syntax</strong> allowed here. "
            "This is the full text message.</p>",
            "status": "fixed",
            "severity": "info",
            "summary": "a summary of the message",
        },
        {
            "date": datetime.datetime(2023, 1, 15, 11, 27, 13),
            "entries": [""],
            "live": False,
            "is_global": True,
            "message_body": "<h1>main message content</h1>\n"
            "<p>Wider <strong>markdown syntax</strong> allowed here.</p>",
            "status": "fixed",
            "severity": "critical",
            "summary": "A **brief description** of the message",
        },
    ]
    loaded_msgs = messages.load_messages(msg_root)
    assert loaded_msgs == expected_msgs
