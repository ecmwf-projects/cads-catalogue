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
import hashlib
import html.parser
import json
import mimetypes
import multiprocessing as mp
import pathlib
import string
import urllib.parse
from collections import ChainMap as _ChainMap
from typing import Any, Dict

from sqlalchemy import inspect

_sentinel_dict: Dict[str, str] = {}


class CADSTemplateKeyError(Exception):
    """Exception raised in case missing interpolation key in CADSTemplate."""

    pass


class CADSTemplate(string.Template):
    """template using only brace brackets for variables."""

    idpattern = "nothing^"  # so force to use curly braces
    braceidpattern = r"(?a:[_a-z][_a-z0-9]*)"

    def substitute(self, mapping=_sentinel_dict, /, **kws):
        # note: adjusted from the method in the standard library
        if mapping is _sentinel_dict:
            mapping = kws
        elif kws:
            mapping = _ChainMap(kws, mapping)

        # Helper function for .sub()
        def convert(mo):
            # check the most common path first
            named = mo.group("braced")
            if mo.group("braced") is not None:
                if named not in mapping:
                    raise CADSTemplateKeyError(
                        f"missing key '{named}', template cannot be rendered."
                    )
                return str(mapping[named])
            # other cases
            if mo.group("escaped") is not None or mo.group("invalid") is not None:
                return mo.group()
            raise ValueError("Unrecognized named group in pattern", self.pattern)

        return self.pattern.sub(convert, self.template)


def list_render(
    input_list: list[Any], context: dict[str, Any], template_class=CADSTemplate
) -> list[Any]:
    """
    render values of an input list according to values defined in a context dictionary.

    :param input_list: list with values to be rendered
    :param context: dictionary with values to be used for rendering
    :param template_class: class to be used for templating
    :return: input_list with values rendered
    """
    output_list = []
    for item in input_list:
        output_item = item
        if isinstance(item, str):
            output_item = template_class(item).substitute(context)
        elif isinstance(item, dict):
            output_item = dict_render(item, context, template_class)
        elif isinstance(item, list):
            output_item = list_render(item, context, template_class)
        output_list.append(output_item)
    return output_list


def dict_render(
    input_dict, context: dict[str, Any], template_class=CADSTemplate
) -> dict[str, Any]:
    """
    render values of an input dictionary according to values defined in a context dictionary.

    :param input_dict: dictionary with values to be rendered
    :param context: dictionary with values to be used for rendering
    :param template_class: class to be used for templating
    :return: a_dict with values rendered
    """
    output_dict = dict()
    for key, value in input_dict.items():
        output_dict[key] = value
        if isinstance(value, str):
            output_dict[key] = template_class(value).substitute(context)
        elif isinstance(value, dict):
            output_dict[key] = dict_render(value, context, template_class)
        elif isinstance(value, list):
            output_dict[key] = list_render(value, context, template_class)
    return output_dict


def is_url(astring):
    """Return True if `astring is parsable as a URL, False otherwise."""
    result = urllib.parse.urlparse(astring)
    if result.scheme and result.netloc:
        return True
    return False


def run_function_with_timeout(timeout, timeout_msg, function, args=(), kwargs=None):
    """Run a function with a timeout inside a child process.

    Raise an error in case of timeout or child process raises an error.

    Parameters
    ----------
    :param timeout: timeout in seconds
    :param timeout_msg: timeout message
    :param function: function to run
    :param args: args of the function
    :param kwargs: kwargs of the function
    """
    if kwargs is None:
        kwargs = dict()
    process = mp.Process(target=function, args=args, kwargs=kwargs)
    process.start()
    process.join(timeout=timeout)
    if process.is_alive():
        process.terminate()
        raise TimeoutError(timeout_msg)
    if process.exitcode == 1:
        # parent process raises as well
        raise ValueError(f"error calling {function.__name__}")


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


def guess_type(file_name, default="application/octet-stream"):
    """Try to guess the mimetypes of a file."""
    guessed = mimetypes.MimeTypes().guess_type(file_name, False)[0]
    return guessed or default


def file2hash(file_path, the_hash=None):
    """Return a MD5 hash object of the file content."""
    if the_hash is None:
        the_hash = hashlib.md5()
    with open(str(file_path), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            the_hash.update(chunk)
    return the_hash


def folder2hash(folder_path, the_hash=None, ignore_names=(".git",)):
    """Return a MD5 hash object of the folder contents."""
    if the_hash is None:
        the_hash = hashlib.md5()
    for path in sorted(
        pathlib.Path(folder_path).iterdir(), key=lambda p: str(p).lower()
    ):
        if path.name in ignore_names:
            continue
        the_hash.update(path.name.encode())
        if path.is_file():
            the_hash = file2hash(path, the_hash)
        elif path.is_dir():
            the_hash = folder2hash(path, the_hash)
    return the_hash


def folders2hash(folder_paths, the_hash=None, ignore_names=(".git",)):
    """Return a MD5 hash object of a list of folders."""
    ret_value = the_hash
    for folder_path in folder_paths:
        ret_value = folder2hash(
            folder_path, the_hash=ret_value, ignore_names=ignore_names
        )
    return ret_value


def normalize_abstract(text: str) -> str:
    """Normalize a string containing html codes."""
    if not text:
        return text
    replacer_map = {"sup": superscript_text, "sub": subscript_text}
    parser = TagReplacer(replacer_map)
    parser.feed(text)
    parser.close()
    return parser.output_text


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


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


def sorted_by_isoformats(
    thelist: list[Any],
    time_attr: str | None = None,
    time_key: str | None = None,
    reverse: bool = False,
) -> list[Any]:
    """Return thelist sorted by an isoformatted datetimes attribute or key."""

    def isodate_sort_key(date_str) -> datetime.datetime:
        date_obj = datetime.datetime.fromisoformat(date_str)
        if date_obj.tzinfo is None:
            date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
        return date_obj

    if time_attr and time_key:
        ValueError("cannot specify both time_attr and time_key")
    if time_attr:
        return sorted(
            thelist,
            key=lambda i: isodate_sort_key(getattr(i, time_attr)),
            reverse=reverse,
        )
    if time_key:
        return sorted(
            thelist, key=lambda i: isodate_sort_key(i[time_key]), reverse=reverse
        )
    raise ValueError("must specify one between time_attr and time_key")
