"""module for entry points."""

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
import html.parser
import json
import logging
import mimetypes
import pathlib
import subprocess
import sys
from typing import Any

import structlog
from sqlalchemy import inspect


class TagReplacer(html.parser.HTMLParser):
    """Translate a html text replacing tag data by some functions."""

    def __init__(self, replacer_map):
        super(TagReplacer, self).__init__()
        self.replacer_map = replacer_map
        self.default_replace = lambda t: t
        self.replacer = self.default_replace
        self.output_text = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.replacer_map:
            self.replacer = self.replacer_map[tag]

    def handle_endtag(self, tag):
        self.replacer = self.default_replace

    def handle_data(self, data):
        self.output_text += self.replacer(data)


def compare_resources_with_dumped_file(
    records, file_path, exclude_fields=("record_update", "resource_id")
):
    """Use for testing records with dumped versions on files."""
    dict_resources = [object_as_dict(r) for r in records]
    #  uncomment following 2 lines to generate the expected file
    # with open(file_path, "w") as fp:
    #     json.dump(dict_resources, fp, default=str, indent=4)
    with open(file_path) as fp:
        expected_resources = json.load(fp)
    for i, resource in enumerate(dict_resources):
        for key in resource:
            if key in exclude_fields:
                continue
            expected_resource = [
                r
                for r in expected_resources
                if r["resource_uid"] == resource["resource_uid"]
            ][0]
            value = resource[key]
            if isinstance(value, datetime.date):
                value = value.isoformat()
            assert value == expected_resource[key], key


def get_last_commit_hash(git_folder: str | pathlib.Path):
    """Return the hash of the last commit done on the repo of the input folder."""
    cmd = 'git log -n 1 --pretty=format:"%H"'
    proc = subprocess.Popen(
        cmd, cwd=git_folder, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    if proc.returncode != 0:
        raise ValueError(err.decode("utf-8"))
    return out.decode("ascii").strip()


def guess_type(file_name, default="application/octet-stream"):
    """Try to guess the mimetypes of a file."""
    guessed = mimetypes.MimeTypes().guess_type(file_name, False)[0]
    return guessed or default


def normalize_abstract(text: str) -> str:
    """Normalize a string containing html codes."""
    if not text:
        return text
    replacer_map = {"sup": superscript_text, "sub": subscript_text}
    parser = TagReplacer(replacer_map)
    parser.feed(text)
    return parser.output_text


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def configure_log(
    loglevel=logging.INFO, logfmt="%(message)s", timefmt="%Y-%m-%d %H:%M.%S"
):
    """Configure the log for the package."""
    logging.basicConfig(
        level=loglevel,
        format=logfmt,
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt=timefmt),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def str2bool(value: str, raise_if_unknown=True, default=False):
    """Return boolean parsing of the string."""
    if value.lower() in ["t", "true", "1", "yes", "y"]:
        return True
    if value.lower() in ["f", "false", "0", "no", "n"]:
        return False
    if raise_if_unknown:
        raise ValueError("unparsable value for boolean: %r" % value)
    return default


def subscript_text(text: str) -> str:
    """Subscript a text."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    sub_s = "ₐ₈CDₑբGₕᵢⱼₖₗₘₙₒₚQᵣₛₜᵤᵥwₓᵧZₐ♭꜀ᑯₑբ₉ₕᵢⱼₖₗₘₙₒₚ૧ᵣₛₜᵤᵥwₓᵧ₂₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"
    res = text.maketrans("".join(normal), "".join(sub_s))
    return text.translate(res)


def superscript_text(text: str) -> str:
    """Superscript a text."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    super_s = "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    res = text.maketrans("".join(normal), "".join(super_s))
    return text.translate(res)
