"""utility module to clone git repositories."""
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

import os
import pathlib
import tempfile
import urllib.parse
from typing import Any, Dict, List, Optional

import git
import structlog
import yaml

logger = structlog.get_logger(__name__)


def add_pat_to_url(url: str) -> str:
    """
    Try to add a personal access token to the given git url.

    :param url: input git url
    """
    # assume variables CADS_PAT/CDS_PAT on environment
    pat_url_map = {
        "github.com/ecmwf-projects": "CADS_PAT",
        "git.ecmwf.int": "CDS_PAT",
    }
    for url_portion, env_var in pat_url_map.items():
        if url_portion in url:
            url_obj = urllib.parse.urlparse(url)
            if url_obj.username is None:
                pat = os.getenv(env_var, "")
                if not pat:
                    return url
                return url_obj._replace(netloc=f"{pat}@{url_obj.netloc}").geturl()
    return url


def get_last_commit_hash(git_folder: str | pathlib.Path):
    """Return the hash of the last commit done on the repo of the input folder."""
    repo = git.Repo(git_folder)
    return repo.head.object.hexsha


def get_repo_url(git_folder: str | pathlib.Path):
    """Return something like 'repo_host:repo_path' of an url of a git remote origin."""
    repo = git.Repo(git_folder)
    remote_url = repo.remotes.origin.url
    urlobj = urllib.parse.urlparse(remote_url)
    if not urlobj.scheme:
        # remote_url like 'git@github.com:ecmwf-projects/cads-catalogue.git'
        repo_url = urlobj.path.split("@", 1)[1]
    else:
        # remote_url like 'https://user@github.com/ecmwf-projects/cads-catalogue.git'
        repo_url = f"{urlobj.hostname}:{urlobj.path.lstrip('/')}"
    return repo_url


def get_git_hashes(folder_map: dict[str, str]) -> Dict[str, str]:
    """
    Return last commit hashes of labelled folders.

    Parameters
    ----------
    folder_map: {'folder_label': 'folder_path'}

    Returns
    -------
    {'folder_label': 'git_hash'}
    """
    current_hashes = dict()
    for folder_label, folder_path in folder_map.items():
        try:
            current_hashes[folder_label] = get_last_commit_hash(folder_path)
        except Exception:  # noqa
            logger.exception(
                f"no check on commit hash for folder '{folder_path}, error follows"
            )
            current_hashes[folder_label] = None
    return current_hashes


def parse_repos_config(
    repo_config_path: str, filtering_kwargs: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Parse file containing information of repositories to clone.

    :param repo_config_path: path to the config file of repositories
    :param filtering_kwargs: filtering kwargs of the catalogue manager
    :return: dictionary of information parsed
    """
    ret_value: dict[str, Any] = dict()
    if not filtering_kwargs:
        filtering_kwargs = dict()
    # base extraction and validation
    if not repo_config_path or not os.path.exists(repo_config_path):
        raise ValueError("config file of repositories to clone not found!")
    logger.info(f"reading config file of repositories {repo_config_path}")
    with open(repo_config_path) as fp:
        try:
            data = yaml.load(fp.read(), Loader=yaml.loader.BaseLoader)
        except Exception:  # noqa
            raise ValueError(
                f"config file of repositories {repo_config_path} is not a valid YAML"
            )
    if data is None:
        raise ValueError(f"config file of repositories {repo_config_path} is empty")

    # note: multiple repositories in the file are supported for all sections,
    # (not only 'cads-forms-json'), due that some remote branches may not exist.
    # After all the clones, actual multiple repositories must be checked.

    # actual parsing of file sections
    default_branch = data["default_branch"]
    for filter_name, repo_category in [
        ("exclude_resources", "cads-forms-json"),
        ("exclude_licences", "cads-licences"),
        ("exclude_resources", "cads-forms-cim-json"),
        ("exclude_messages", "cads-messages"),
        ("exclude_contents", "cads-contents-json"),
    ]:
        if not filtering_kwargs.get(filter_name, False):
            ret_value[repo_category] = []
            if repo_category not in data or not len(data[repo_category]):
                raise ValueError(
                    f"config file of repositories {repo_config_path} not valid: "
                    f"not found any repository for section {repo_category}"
                )
            for repo_md in data[repo_category]:
                repo_item = {
                    "url": repo_md["url"],
                    "branch": repo_md.get("branch", default_branch),
                }
                ret_value[repo_category].append(repo_item)
    # consider section "cads-configuration" optional
    repo_category = "cads-configuration"
    if repo_category not in data or not len(data[repo_category]):
        return ret_value
    ret_value[repo_category] = []
    for repo_md in data[repo_category]:
        repo_item = {
            "url": repo_md["url"],
            "branch": repo_md.get("branch", default_branch),
        }
        ret_value[repo_category].append(repo_item)
    return ret_value


def clone_repository(
    repo_url: str,
    repo_branch: Optional[str] = None,
    repo_path: Optional[str] = None,
    multi_options: tuple[str, ...] = ("--depth=1", "--recurse-submodules"),
    delete_remote: bool = False,
    root_path: Optional[str] = None,
) -> str:
    """
    Clone a git repository `repo_url` on folder `repo_path`.

    :param repo_url: git remote url
    :param repo_branch: branch to clone
    :param repo_path: destination folder
    :param multi_options: options for cloning
    :param delete_remote: if True, delete given git remote
    :param root_path: if `repo_path` not specified, create temp dir inside this folder
    :return: path of cloned repository
    """
    repo_name = os.path.splitext(os.path.basename(repo_url))[0]
    if not repo_path:
        repo_path = tempfile.mkdtemp(prefix=f"{repo_name}_", dir=root_path)
    if repo_branch:
        multi_options += (f"--branch {repo_branch}",)
    repo_url = add_pat_to_url(repo_url)
    repo = git.Repo.clone_from(repo_url, repo_path, multi_options=list(multi_options))
    if delete_remote:
        repo.delete_remote(repo.remote())
    try:
        reference_tag = repo.active_branch.name
        logger.info(
            f"cloned repo {repo_name!r} branch {reference_tag!r} in path {repo_path!r}"
        )
    except TypeError:
        reference_tag = next(
            (tag for tag in repo.tags if tag.commit == repo.head.commit)
        ).name
        logger.info(
            f"cloned repo {repo_name!r} tag {reference_tag!r} in path {repo_path!r}"
        )
    return repo_path


def clone_repositories(
    repos_info: dict[str, Any], root_path: Optional[str] = None
) -> dict[str, Any]:
    """
    Clone a set of repositories in local filesystem.

    :param repos_info: repositories to clone as returned by parse_repos_config
    :param root_path: folder path where to include all cloned repositories
    """
    repos_info_cloned: dict[str, List[dict[str, str]]] = dict()
    for repo_category in repos_info:
        repos_info_cloned[repo_category] = []
        for repo_md in repos_info[repo_category]:
            repo_url = repo_md["url"]
            repo_branch = repo_md["branch"]
            try:
                clone_path = clone_repository(
                    repo_url, repo_branch, root_path=root_path
                )
                repos_info_cloned[repo_category].append(
                    {"url": repo_url, "branch": repo_branch, "clone_path": clone_path}
                )
            except git.GitCommandError as error:
                if "ould not find remote branch" in error.stderr.lower():  # bleah!
                    # branch not found is tolerated
                    logger.warning(
                        f"clone of {repo_url} failed, not found remote branch '{repo_branch}'"
                    )
                else:
                    logger.exception(f"clone of {repo_url} failed, error follows")
                    raise
            except:
                logger.exception(f"clone of {repo_url} failed, error follows")
                raise
    for repo_category in repos_info_cloned:
        if (
            len(repos_info_cloned[repo_category]) > 1
            and repo_category != "cads-forms-json"
        ):
            raise ValueError(
                f"repo configuration error: more than 1 source for {repo_category} is not supported"
            )
        if not len(repos_info_cloned[repo_category]):
            raise ValueError(f"no repository for {repo_category} has been cloned")
    return repos_info_cloned
