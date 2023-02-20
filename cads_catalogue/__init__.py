"""CADS catalogue manager."""

# Copyright 2022, European Union.
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

try:
    # NOTE: the `version.py` file must not be present in the git repository
    #   as it is generated by setuptools at install time
    from .version import __version__
except ImportError:  # pragma: no cover
    # Local copy or not installed with setuptools
    __version__ = "999"

from .database import Licence, Resource, ResourceLicence, init_database
from .entry_points import info, main, update_catalogue
from .manager import load_licences_from_folder, load_resource_from_folder

__all__ = [
    "__version__",
    "ResourceLicence",
    "Resource",
    "Licence",
    "init_database",
    "load_licences_from_folder",
    "load_resource_from_folder",
    "info",
    "update_catalogue",
    "main",
]
