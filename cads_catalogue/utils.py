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

from typing import Any

from sqlalchemy import inspect


def object_as_dict(obj: Any) -> dict[str, Any]:
    """Convert a sqlalchemy object in a python dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def recursive_key_search(
    obj: Any,
    key: str,
    current_result: list[Any] | None = None,
) -> list[Any]:
    """Crowl inside input dictionary/list searching for all keys=key for each dictionary found.

    Note that it does not search inside values of the key found.

    Parameters
    ----------
    obj: input dictionary or list
    key: key to search
    current_result: list of results where aggregate what found on

    Returns
    -------
    list of found values
    """
    if current_result is None:
        current_result = []
    if isinstance(obj, dict):
        for current_key, current_value in obj.items():
            if current_key == key:
                current_result.append(current_value)
            else:
                current_result = recursive_key_search(
                    current_value, key, current_result
                )
    elif isinstance(obj, list):
        for item in obj:
            current_result = recursive_key_search(item, key, current_result)
    return current_result


def str2bool(value: str, raise_if_unknown=True, default=False):
    """Return boolean parsing of the string."""
    if value.lower() in ["t", "true", "1", "yes", "y"]:
        return True
    if value.lower() in ["f", "false", "0", "no", "n"]:
        return False
    if raise_if_unknown:
        raise ValueError("unparsable value for boolean: %r" % value)
    return default
