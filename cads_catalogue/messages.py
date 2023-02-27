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

import datetime
import logging
import os
import pathlib
from typing import Any, List

import markdown

from cads_catalogue import utils

logger = logging.getLogger(__name__)


def md2message_record(msg_path, is_global) -> dict[str, Any]:
    """
    Load message record from a markdown file.

    Parameters
    ----------
    msg_path: path to the message markdown file
    is_global: True if message must be considered global, False otherwise

    Returns
    -------
    dictionary of information parsed.
    """
    with open(msg_path) as fp:
        text = fp.read()
    md_obj = markdown.Markdown(extensions=["meta"])
    content = md_obj.convert(text).strip()
    header_obj = md_obj.Meta  # type: ignore
    msg_record = {
        "date": datetime.datetime.strptime(header_obj["date"][0], "%Y-%m-%dT%H:%M:%SZ"),
        "summary": " ".join(header_obj.get("summary", [""])).strip(),
        "severity": header_obj.get("severity", ["info"])[0],
        "live": utils.str2bool(header_obj.get("live", ["false"])[0]),
        "is_global": is_global,
        "content": content,
        "status": header_obj.get("status", ["ongoing"])[0],
        # this is not a db field
        "entries": [e.strip() for e in header_obj.get("entries", [""])[0].split(",")],
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
    global_folder = os.path.join(root_msg_folder, "global")
    for is_global, root_folder in [(False, contents_folder), (True, global_folder)]:
        for current_root, dirs, files in os.walk(root_folder):
            for current_file in files:
                file_path = os.path.join(current_root, current_file)
                if os.path.splitext(current_file)[1].lower() == ".md":
                    try:
                        msg_record = md2message_record(file_path, is_global=is_global)
                    except:  # noqa
                        logger.exception("error loading message %r" % file_path)
                        continue
                    loaded_messages.append(msg_record)
                else:
                    logger.warning("file at path %r will not be parsed" % file_path)
    return loaded_messages
