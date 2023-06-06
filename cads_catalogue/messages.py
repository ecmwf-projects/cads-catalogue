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
from typing import Any, List, Sequence

import frontmatter
import sqlalchemy as sa
import structlog

import cads_catalogue

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
logger = structlog.get_logger(__name__)


def message_sync(
    session: sa.orm.session.Session,
    msg: dict[str, Any],
) -> cads_catalogue.database.Message:
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
    # NOTE: portal messages have always entries = []
    entries = message.pop("entries", [])

    # translate entries in resource_objs
    msg_resource_objs: Sequence[cads_catalogue.database.Resource] = []
    clauses = []
    for entry in entries:
        if "xxx" in entry:
            pattern = entry.replace("xxx", "%")
            clauses.append(cads_catalogue.database.Resource.resource_uid.like(pattern))
        else:
            clauses.append(cads_catalogue.database.Resource.resource_uid == entry)
    if clauses:
        clause = sa.or_(*clauses)
        msg_resource_objs = session.scalars(
            sa.select(cads_catalogue.database.Resource).filter(clause)
        ).all()
        if not msg_resource_objs:
            logger.warning(
                f"message {message_uid} with entries '{entries}' is unrelated to any dataset"
            )
    # upsert of the message
    db_message = session.scalars(
        sa.select(cads_catalogue.database.Message)
        .filter_by(message_uid=message_uid)
        .limit(1)
    ).first()
    if not db_message:
        db_message = cads_catalogue.database.Message(**message)
        session.add(db_message)
        logger.debug("added db message %r" % message_uid)
    else:
        session.execute(
            sa.update(cads_catalogue.database.Message)
            .filter_by(message_id=db_message.message_id)
            .values(**message)
        )
        logger.debug("updated db message %r" % message_uid)

    # update of the message's resources
    db_message.resources = msg_resource_objs  # type: ignore
    return db_message


def md2message_record(msg_path, msg_uid, **record_attrs) -> dict[str, Any]:
    """
    Load message record from a markdown file.

    Parameters
    ----------
    msg_path: path to the message markdown file
    msg_uid: uid of the message record
    record_attrs: force values to some fields of output record

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
        "content": md_obj.content.strip(),
        # this is not a db field
        "entries": [e.strip() for e in md_obj.get("entries", "").split(",")],
    }
    msg_record.update(record_attrs)
    if msg_record.get("is_global", False):
        msg_record["entries"] = []
    # some validations
    if not msg_record["summary"] and not msg_record["content"]:
        raise ValueError(
            "both summary and message body (content) empty on %r" % msg_path
        )
    if msg_record["severity"] not in ("info", "warning", "critical", "success"):
        raise ValueError(
            "%r is not a valid value for severity" % msg_record["severity"]
        )
    if not msg_record["is_global"] and not msg_record["entries"]:
        raise ValueError("expected a values for entries, found empty")
    return msg_record


def load_contents_messages(
    root_msg_folder: str | pathlib.Path, contents_folder: str | pathlib.Path
) -> List[dict[str, Any]]:
    """
    Look for messages specific for a subset of datasets (i.e. not 'global').

    Parameters
    ----------
    contents_folder: root path where to look for messages (i.e. cads-messages/contents root folder)
    root_msg_folder: base root path (i.e. cads-messages root folder) (used to generate msg uids)

    Returns
    -------
    List of found messages parsed.
    """
    loaded_messages: List[dict[str, Any]] = []

    for current_root, dirs, files in os.walk(contents_folder):
        for current_file in files:
            file_path = os.path.join(current_root, current_file)
            if os.path.splitext(current_file)[1].lower() == ".md":
                msg_uid = os.path.relpath(file_path, root_msg_folder)
                try:
                    msg_record = md2message_record(file_path, msg_uid, is_global=False)
                except:  # noqa
                    logger.exception("error loading message %r" % file_path)
                    continue
                loaded_messages.append(msg_record)
            else:
                logger.warning("file at path %r will not be parsed" % file_path)
    return loaded_messages


def load_portal_messages(
    root_msg_folder: str | pathlib.Path, portal_folder: str | pathlib.Path
) -> List[dict[str, Any]]:
    """
    Look for messages specific for a portal (i.e. 'global' messages).

    Parameters
    ----------
    root_msg_folder: base root path (i.e. cads-messages root folder) (used to generate msg uids)
    portal_folder: root path where to look for portal messages

    Returns
    -------
    List of found messages parsed.
    """
    loaded_messages: List[dict[str, Any]] = []
    portal = os.path.basename(portal_folder)
    for current_root, dirs, files in os.walk(portal_folder):
        for current_file in files:
            file_path = os.path.join(current_root, current_file)
            if os.path.splitext(current_file)[1].lower() == ".md":
                msg_uid = os.path.relpath(file_path, root_msg_folder)
                try:
                    msg_record = md2message_record(
                        file_path, msg_uid, is_global=True, portal=portal
                    )
                except:  # noqa
                    logger.exception("error loading message %r" % file_path)
                    continue
                loaded_messages.append(msg_record)
            else:
                logger.warning("file at path %r will not be parsed" % file_path)
    return loaded_messages


def load_messages(root_msg_folder: str | pathlib.Path) -> List[dict[str, Any]]:
    """
    Load all messages from a well-known filesystem root.

    Parameters
    ----------
    root_msg_folder: root path where to look for messages (i.e. cads-messages root folder)

    Returns
    -------
    List of found messages parsed.
    """
    loaded_messages: List[dict[str, Any]] = []
    # load 'contents' folder
    contents_folder = os.path.join(root_msg_folder, "contents")
    if os.path.isdir(contents_folder):
        loaded_messages += load_contents_messages(root_msg_folder, contents_folder)
    else:
        logger.warning("not found folder %r" % contents_folder)

    # load 'portals' folder
    portals_folder = os.path.join(root_msg_folder, "portals")
    if os.path.isdir(portals_folder):
        for portal in os.listdir(portals_folder):
            portal_folder = os.path.join(portals_folder, portal)
            if not os.path.isdir(portal_folder):
                continue
            loaded_messages += load_portal_messages(root_msg_folder, portal_folder)
    else:
        logger.warning("not found folder %r" % portals_folder)

    return loaded_messages


def update_catalogue_messages(
    session: sa.orm.session.Session,
    messages_folder_path: str | pathlib.Path,
    remove_orphans: bool = True,
):
    """
    Load metadata of messages from files and sync each message in the db.

    Parameters
    ----------
    session: opened SQLAlchemy session
    messages_folder_path: path to the root folder containing metadata files for system messages
    remove_orphans: if True, remove from the database other messages not involved (default True)

    Returns
    -------
    list: list of message uids involved
    """
    logger.info("running catalogue db update for messages")
    # load metadata of messages from files and sync each messages in the db
    msgs = load_messages(messages_folder_path)
    logger.info("loaded %s messages from folder %s" % (len(msgs), messages_folder_path))
    involved_msg_ids = []
    for msg in msgs:
        msg_uid = msg["message_uid"]
        involved_msg_ids.append(msg_uid)
        try:
            with session.begin_nested():
                message_sync(session, msg)
            logger.info("message %s db sync successful" % msg_uid)
        except Exception:  # noqa
            logger.exception("db sync for message %s failed, error follows" % msg_uid)

    if not remove_orphans:
        return involved_msg_ids

    # remove not loaded messages from the db
    msgs_to_delete = session.scalars(
        sa.select(cads_catalogue.database.Message).filter(
            cads_catalogue.database.Message.message_uid.notin_(involved_msg_ids)
        )
    )
    for msg_to_delete in msgs_to_delete:
        msg_to_delete.resources = []
        session.delete(msg_to_delete)
        logger.debug("removed old message %s" % msg_to_delete.message_uid)

    return involved_msg_ids
