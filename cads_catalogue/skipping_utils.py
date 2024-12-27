"""skipping utilities for the catalogue manager."""

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

import os.path

import structlog

from cads_catalogue import contents, manager

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
CATALOGUE_DIR = os.path.abspath(os.path.join(THIS_PATH, ".."))
PACKAGE_DIR = os.path.abspath(
    os.path.join(
        CATALOGUE_DIR,
        "..",
    )
)

logger = structlog.get_logger(__name__)


def can_skip_licences(new_git_hashes, last_run_status, force, filtering_kwargs):
    """Return True if catalogue manager can skip licences' processing."""
    if filtering_kwargs["exclude_licences"]:
        logger.info("update of licences skipped, detected option to exclude licences.")
        return True
    if force:
        logger.info("update of licences not skippable, detected force mode.")
        return False
    if new_git_hashes["licence_repo_commit"] != last_run_status.get(
        "licence_repo_commit"
    ):
        logger.info(
            "update of licences not skippable, detected update of licences repository."
        )
        return False
    if new_git_hashes["licence_repo_commit"] is None:
        logger.info("update of licences not skippable, git hash not recoverable.")
        return False
    logger.info(
        "update of licences skipped: source files have not changed. Use --force to update anyway."
    )
    return True


def can_skip_datasets(
    new_git_hashes, last_run_status, force, filtering_kwargs, to_process
):
    """Return True if catalogue manager can skip datasets' processing."""
    if filtering_kwargs["exclude_resources"]:
        logger.info("update of datasets skipped, detected option to exclude resources.")
        return True
    if "licences" in to_process:
        logger.info("update of datasets not skippable due updating of licences.")
        return False
    if force:
        logger.info("update of datasets not skippable, detected force mode.")
        return False
    if new_git_hashes["metadata_repo_commit"] != last_run_status.get(
        "metadata_repo_commit"
    ):
        logger.info(
            "update of datasets not skippable, detected update of datasets repository."
        )
        return False
    if new_git_hashes["metadata_repo_commit"] is None:
        logger.info(
            "update of datasets not skippable, git hash of datasets repository not recoverable."
        )
        return False
    if new_git_hashes["cim_repo_commit"] != last_run_status.get("cim_repo_commit"):
        logger.info(
            "update of datasets not skippable, detected update of cim datasets repository."
        )
        return False
    if new_git_hashes["cim_repo_commit"] is None:
        logger.info(
            "update of datasets not skippable, git hash of cim datasets repository not recoverable."
        )
        return False
    logger.info(
        "update of datasets skipped: source files have not changed. Use --force to update anyway."
    )
    return True


def can_skip_messages(
    new_git_hashes, last_run_status, force, filtering_kwargs, to_process
):
    """Return True if catalogue manager can skip messages' processing."""
    if filtering_kwargs["exclude_messages"]:
        logger.info("update of messages skipped, detected option to exclude messages.")
        return True
    if "datasets" in to_process:
        logger.info("update of messages not skippable due updating of datasets.")
        return False
    if force:
        logger.info("update of messages not skippable, detected force mode.")
        return False
    if new_git_hashes["message_repo_commit"] != last_run_status.get(
        "message_repo_commit"
    ):
        logger.info(
            "update of messages not skippable, detected update of messages repository."
        )
        return False
    if new_git_hashes["message_repo_commit"] is None:
        logger.info("update of messages not skippable, git hash not recoverable.")
        return False
    logger.info(
        "update of messages skipped: source files have not changed. Use --force to update anyway."
    )
    return True


def can_skip_contents(
    new_git_hashes, last_run_status, force, filtering_kwargs, contents_config
):
    """Return True if catalogue manager can skip contents' processing."""
    if filtering_kwargs["exclude_contents"]:
        logger.info("update of contents skipped, detected option to exclude contents.")
        return True
    if contents_config != last_run_status.get("contents_config"):
        logger.info(
            "update of contents not skippable, detected update of contents configuration."
        )
        return False
    if force:
        logger.info("update of contents not skippable, detected force mode.")
        return False
    if new_git_hashes["content_repo_commit"] != last_run_status.get(
        "content_repo_commit"
    ):
        logger.info(
            "update of contents not skippable, detected update of contents repository."
        )
        return False
    if new_git_hashes["content_repo_commit"] is None:
        logger.info("update of contents not skippable, git hash not recoverable.")
        return False
    logger.info(
        "update of contents skipped: source files have not changed. Use --force to update anyway."
    )
    return True


def skipping_engine(
    session_obj,
    config_paths,
    force,
    repo_paths,
    filtering_kwargs,
):
    """
    Return useful information for catalogue manager about what to skip processing.

    returns (to_process, new_catalogue_update_md, force), where:
    to_process: list of what to process (one or more among 'datasets', 'licences', 'messages', 'contents'),
    new_catalogue_update_md: new record to be applied to the table catalogue_updates:
    force: force option to be applied
    """
    to_process = ["licences", "datasets", "messages", "contents"]
    new_override_md = manager.parse_override_md(config_paths["overrides_path"])
    new_contents_config = contents.yaml2context(config_paths["contents_config_path"])

    logger.info("comparing current input files with the ones of the last run")
    folders_map = {
        # db column: folder path
        "catalogue_repo_commit": CATALOGUE_DIR,
        "metadata_repo_commit": repo_paths["metadata_repo"],
        "cim_repo_commit": repo_paths["cim_repo"],
        "message_repo_commit": repo_paths["message_repo"],
        "licence_repo_commit": repo_paths["licence_repo"],
        "content_repo_commit": repo_paths["content_repo"],
    }
    new_git_hashes = manager.get_git_hashes(folders_map)
    new_catalogue_update_md = {
        "override_md": new_override_md,
        "contents_config": new_contents_config,
        "catalogue_repo_commit": new_git_hashes["catalogue_repo_commit"],
    }
    with session_obj.begin() as session:  # type: ignore
        last_run_status = manager.get_status_of_last_update(session)
    if (
        new_git_hashes["catalogue_repo_commit"]
        != last_run_status.get("catalogue_repo_commit")
        or new_git_hashes["catalogue_repo_commit"] is None
    ):
        logger.info(
            "detected update of cads-catalogue repository. Imposing automatic --force mode."
        )
        force = True
    if new_override_md != last_run_status.get("override_md"):
        logger.info(
            "detected update of override information. Imposing automatic --force mode."
        )
        force = True
    if can_skip_licences(new_git_hashes, last_run_status, force, filtering_kwargs):
        to_process.remove("licences")
    else:
        new_catalogue_update_md["licence_repo_commit"] = new_git_hashes[
            "licence_repo_commit"
        ]
    if can_skip_datasets(
        new_git_hashes, last_run_status, force, filtering_kwargs, to_process
    ):
        to_process.remove("datasets")
    else:
        is_filter_datasets_enabled = (
            filtering_kwargs["include"]
            or filtering_kwargs["exclude"]
            or filtering_kwargs["exclude_resources"]
        )
        if not is_filter_datasets_enabled:
            new_catalogue_update_md["metadata_repo_commit"] = new_git_hashes[
                "metadata_repo_commit"
            ]
            new_catalogue_update_md["cim_repo_commit"] = new_git_hashes[
                "cim_repo_commit"
            ]
    if can_skip_messages(
        new_git_hashes, last_run_status, force, filtering_kwargs, to_process
    ):
        to_process.remove("messages")
    else:
        new_catalogue_update_md["message_repo_commit"] = new_git_hashes[
            "message_repo_commit"
        ]
    if can_skip_contents(
        new_git_hashes, last_run_status, force, filtering_kwargs, new_contents_config
    ):
        to_process.remove("contents")
    else:
        new_catalogue_update_md["content_repo_commit"] = new_git_hashes[
            "content_repo_commit"
        ]
    return to_process, new_catalogue_update_md, force
