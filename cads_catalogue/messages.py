"""utility module to load and store data in the catalogue database."""

# Copyright 2023, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pathlib
from typing import Any, Dict, List

import frontmatter
import structlog
from sqlalchemy.orm.session import Session

from cads_catalogue import database

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
logger = structlog.get_logger(__name__)


def message_sync(
    session: Session,
    msg: dict[str, Any],
) -> database.Message:
    """
    Compare db record and file of a message and make them the same.

    Parameters
    ----------
    session: opened SQLAlchemy session
    msg: metadata of loaded message

    Returns
    -------
    The created/updated db message
    """
    message = msg.copy()
    message_uid = message["message_uid"]
    resource_uids = message.pop("entries")
    db_resources: Dict[str, Any] = dict()
    if not message["is_global"]:
        for resource_uid in resource_uids:
            if "xxx" in resource_uid:
                pattern = resource_uid.replace("xxx", "%")
                clause = database.Resource.resource_uid.like(pattern)
            else:
                clause = database.Resource.resource_uid == resource_uid
            for resource_obj in session.query(database.Resource).filter(clause):
                if not resource_obj:
                    raise ValueError("resource_uid = %r not found" % resource_uid)
                db_resources[resource_uid] = db_resources.get(resource_uid, [])
                db_resources[resource_uid].append(resource_obj)

    db_message = (
        session.query(database.Message).filter_by(message_uid=message_uid).first()
    )
    if not db_message:
        db_message = database.Message(**message)
        session.add(db_message)
        logger.debug("added db message %r" % message_uid)
    else:
        session.query(database.Message).filter_by(
            message_id=db_message.message_id
        ).update(message)
        logger.debug("updated db message %r" % message_uid)

    db_message.resources = []  # type: ignore
    if not message["is_global"]:
        for resource_uid in resource_uids:
            for resource_obj in db_resources[resource_uid]:
                db_message.resources.append(resource_obj)  # type: ignore
    return db_message


def md2message_record(msg_path, msg_uid, is_global) -> dict[str, Any]:
    """
    Load message record from a markdown file.

    Parameters
    ----------
    msg_path: path to the message markdown file
    msg_uid: uid of the message record
    is_global: True if message must be considered global, False otherwise

    Returns
    -------
    dictionary of information parsed.
    """
    md_obj = frontmatter.load(msg_path)
    msg_record = {
        "message_uid": msg_uid,
        "date": md_obj["date"].replace(tzinfo=None),
        "summary": md_obj.get("summary"),
        "severity": md_obj.get("severity", "info"),
        "live": md_obj.get("live", "false"),
        "is_global": is_global,
        "content": md_obj.content.strip(),
        "status": md_obj.get("status", "ongoing"),
        # this is not a db field
        "entries": [e.strip() for e in md_obj.get("entries", "").split(",")],
    }
    # some validations
    if not msg_record["summary"] and not msg_record["content"]:
        raise ValueError(
            "both summary and message body (content) empty on %r" % msg_path
        )
    if msg_record["severity"] not in ("info", "warning", "critical", "success"):
        raise ValueError(
            "%r is not a valid value for severity" % msg_record["severity"]
        )
    if msg_record["status"] not in ("ongoing", "closed", "fixed"):
        raise ValueError("%r is not a valid value for status" % msg_record["status"])
    if not msg_record["is_global"] and not msg_record["entries"]:
        raise ValueError("expected a values for entries, found empty")
    return msg_record


def load_messages(root_msg_folder: str | pathlib.Path) -> List[dict[str, Any]]:
    """
    Load messages from a dataset folder or at global level.

    Parameters
    ----------
    root_msg_folder: root path where to look for messages.

    Returns
    -------
    List of found messages parsed.
    """
    loaded_messages: List[dict[str, Any]] = []
    contents_folder = os.path.join(root_msg_folder, "contents")
    global_folder = os.path.join(root_msg_folder, "portal")
    for is_global, root_folder in [(False, contents_folder), (True, global_folder)]:
        if not os.path.isdir(root_folder):
            logger.warning("not found folder %r" % root_folder)
            continue
        for current_root, dirs, files in os.walk(root_folder):
            for current_file in files:
                file_path = os.path.join(current_root, current_file)
                if os.path.splitext(current_file)[1].lower() == ".md":
                    msg_uid = os.path.relpath(file_path, root_msg_folder)
                    try:
                        msg_record = md2message_record(
                            file_path, msg_uid, is_global=is_global
                        )
                    except:  # noqa
                        logger.exception("error loading message %r" % file_path)
                        continue
                    loaded_messages.append(msg_record)
                else:
                    logger.warning("file at path %r will not be parsed" % file_path)
    return loaded_messages
