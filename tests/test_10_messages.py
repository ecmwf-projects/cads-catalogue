import datetime
import operator
import os.path

import sqlalchemy as sa

import cads_catalogue.database
from cads_catalogue import messages

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_MESSAGE_ROOT_PATH = os.path.join(TESTDATA_PATH, "cads-messages")


def test_load_messages() -> None:
    msg_root = TEST_MESSAGE_ROOT_PATH
    expected_msgs = [
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here. This is the full text "
            "message.",
            "date": datetime.datetime(2021, 1, 14, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "show_date": True,
            "message_uid": "sites/cds/2023/Jan/2021-01-example-of-info-active.md",
            "site": "cds",
            "severity": "info",
            "summary": "a summary of the message",
        },
        {
            "content": "# message main body for archived warning message for some "
            "entries \n"
            " \n"
            "Wider **markdown syntax** allowed here. In this example:\n"
            "* *summary* is missing, so only this main body message is used\n"
            "* *status* is missing (indeed actually is not used yet)",
            "date": datetime.datetime(2023, 1, 11, 11, 27, 13),
            "entries": ["reanalysis-era5-xxx", "satellite-surface-radiation-budget"],
            "is_global": False,
            "live": False,
            "show_date": False,
            "message_uid": "contents/2023/2023-01-archived-warning.md",
            "severity": "warning",
            "summary": None,
        },
        {
            "content": "# message main body for active critical message for some "
            "datasets \n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 12, 11, 27, 13),
            "entries": ["reanalysis-era5-land", "satellite-surface-radiation-budget"],
            "is_global": False,
            "live": True,
            "show_date": True,
            "message_uid": "contents/2023/2023-01-era5-issue-456.md",
            "severity": "critical",
            "summary": "example of active critical content message",
        },
        {
            "content": "# message main body for archived critical message for some "
            "datasets \n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 13, 11, 27, 13),
            "entries": ["reanalysis-era5-land", "satellite-surface-xxx"],
            "is_global": False,
            "live": False,
            "show_date": True,
            "message_uid": "contents/foo-bar/this-will-be-also-taken.md",
            "severity": "critical",
            "summary": "example of expired critical content message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 15, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": False,
            "show_date": True,
            "message_uid": "sites/cds/2023/Jan/2023-01-example-of-archived-critical.md",
            "site": "cds",
            "severity": "critical",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 1, 16, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "show_date": False,
            "message_uid": "sites/cds/2023/Jan/2023-01-example-warning-active.md",
            "site": "cds",
            "severity": "warning",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here. This is the full text "
            "message.",
            "date": datetime.datetime(2023, 2, 14, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "show_date": True,
            "message_uid": "sites/ads/2023/02/2021-02-example-of-info-active.md",
            "site": "ads",
            "severity": "info",
            "summary": "a summary of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 2, 15, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": False,
            "show_date": True,
            "message_uid": "sites/ads/2023/02/2023-02-example-of-archived-critical.md",
            "site": "ads",
            "severity": "critical",
            "summary": "A **brief description** of the message",
        },
        {
            "content": "# main message content\n"
            " \n"
            "Wider **markdown syntax** allowed here.",
            "date": datetime.datetime(2023, 2, 16, 11, 27, 13),
            "entries": [],
            "is_global": True,
            "live": True,
            "show_date": True,
            "message_uid": "sites/ads/2023/02/2023-02-example-warning-active.md",
            "site": "ads",
            "severity": "warning",
            "summary": "A **brief description** of the message",
        },
    ]
    loaded_msgs = messages.load_messages(msg_root)
    assert sorted(loaded_msgs, key=operator.itemgetter("date")) == expected_msgs


def test_message_sync(session_obj: sa.orm.sessionmaker) -> None:
    cnt_message = {
        "content": "# message main body for archived critical message for some "
        "datasets \n"
        " \n"
        "Wider **markdown syntax** allowed here.",
        "date": datetime.datetime(2023, 1, 13, 11, 27, 13),
        "entries": ["reanalysis-era5-land", "satellite-surface-xxx"],
        "is_global": False,
        "live": False,
        "show_date": True,
        "message_uid": "contents/foo-bar/this-will-be-also-taken.md",
        "severity": "critical",
        "summary": "example of expired critical content message",
    }
    prt_message = {
        "content": "# main message content\n \nWider **markdown syntax** allowed here.",
        "date": datetime.datetime(2023, 1, 15, 11, 27, 13),
        "entries": [],
        "is_global": True,
        "live": False,
        "show_date": True,
        "message_uid": "sites/cds/2023/Jan/2023-01-example-of-archived-critical.md",
        "site": "site2",
        "severity": "success",
        "summary": "A **brief description** of the message",
    }
    resource1 = {
        "resource_id": 1,
        "resource_uid": "satellite-air-example",
        "abstract": "an abstract",
        "description": "",
        "type": "a type",
        "portal": "portal1",
    }
    resource2 = {
        "resource_id": 2,
        "resource_uid": "satellite-surface-example1",
        "abstract": "an abstract",
        "description": "",
        "type": "a type",
        "portal": "portal1",
    }
    resource3 = {
        "resource_id": 3,
        "resource_uid": "satellite-surface-example2",
        "abstract": "an abstract",
        "description": "",
        "type": "a type",
        "portal": "portal2",
    }
    resource4 = {
        "resource_id": 4,
        "resource_uid": "reanalysis-era5-land",
        "abstract": "an abstract",
        "description": "",
        "type": "a type",
        "portal": "portal2",
    }

    with session_obj() as session:
        # db is empty: adding content message
        db_message1 = messages.message_sync(session, cnt_message)
        session.commit()
        for key, value in cnt_message.items():
            if key == "entries":
                continue
            assert getattr(db_message1, key) == value
        assert db_message1.resources == []

        # adding test resources
        for resource in [resource1, resource2, resource3, resource4]:
            resource_obj = cads_catalogue.database.Resource(**resource)  # type: ignore
            session.add(resource_obj)
        session.commit()

        # changing cnt_message, so do an update
        cnt_message["live"] = False
        db_message2 = messages.message_sync(session, cnt_message)
        session.commit()
        assert db_message1.message_id == db_message2.message_id
        for key, value in cnt_message.items():
            if key == "entries":
                continue
            assert getattr(db_message2, key) == value
        assert sorted([r.resource_id for r in db_message2.resources]) == [2, 3, 4]  # type: ignore

        # adding site message
        db_message3 = messages.message_sync(session, prt_message)
        session.commit()
        for key, value in prt_message.items():
            if key == "entries":
                continue
            assert getattr(db_message3, key) == value
        assert db_message3.resources == []
