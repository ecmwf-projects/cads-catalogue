import os.path

import pytest

from cads_catalogue import repos

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def test_add_pat_to_url(temp_environ):
    # case no PAT on environment -> no url change
    temp_environ.pop("CADS_PAT", default=None)
    temp_environ.pop("CDS_PAT", default=None)
    url = "https://git.ecmwf.int/scm/cds/test-forms-potato.git"
    assert repos.add_pat_to_url(url) == url
    url = "https://github.com/ecmwf-projects/cads-forms-json.git"
    assert repos.add_pat_to_url(url) == url
    url = "https://otherhost.com/ecmwf-projects/cads-forms-apple.git"
    assert repos.add_pat_to_url(url) == url

    # case PAT on environment ...
    temp_environ["CADS_PAT"] = "acadspat"
    temp_environ["CDS_PAT"] = "acdspat"

    # ... but already inside urls -> no url change
    url = "https://anotherpat@git.ecmwf.int/scm/cds/test-forms-potato.git"
    assert repos.add_pat_to_url(url) == url
    url = "https://anotherpat@github.com/ecmwf-projects/cads-forms-json.git"
    assert repos.add_pat_to_url(url) == url
    url = "https://anotherpat@otherhost.com/ecmwf-projects/cads-forms-apple.git"
    assert repos.add_pat_to_url(url) == url

    # ... and missing inside urls -> url changes if belongs to ECMWF
    url = "https://git.ecmwf.int/scm/cds/test-forms-potato.git"
    assert (
        repos.add_pat_to_url(url)
        == "https://acdspat@git.ecmwf.int/scm/cds/test-forms-potato.git"
    )
    url = "https://github.com/ecmwf-projects/cads-forms-json.git"
    assert (
        repos.add_pat_to_url(url)
        == "https://acadspat@github.com/ecmwf-projects/cads-forms-json.git"
    )
    url = "https://otherhost.com/ecmwf-projects/cads-forms-apple.git"
    assert repos.add_pat_to_url(url) == url


def test_parse_repos_config():
    test_config_path = os.path.join(TESTDATA_PATH, "notexist.yaml")
    with pytest.raises(ValueError):
        repos.parse_repos_config(test_config_path, {})

    test_config_path = os.path.join(TESTDATA_PATH, "repos.yaml")
    effective_conf = repos.parse_repos_config(test_config_path, {})
    expected_conf = {
        "cads-forms-json": [
            {
                "url": "https://git.ecmwf.int/scm/cds/test-forms-potato.git",
                "branch": "test",
            },
            {
                "url": "https://git.ecmwf.int/scm/cds/test-forms-apple.git",
                "branch": "dev",
            },
        ],
        "cads-licences": [
            {
                "url": "https://github.com/ecmwf-projects/cads-licences.git",
                "branch": "prod",
            }
        ],
        "cads-forms-cim-json": [
            {
                "url": "https://github.com/ecmwf-projects/cads-forms-cim-json.git",
                "branch": "prod",
            }
        ],
        "cads-messages": [
            {
                "url": "https://github.com/ecmwf-projects/cads-messages.git",
                "branch": "preprod",
            }
        ],
        "cads-contents-json": [
            {
                "url": "https://github.com/ecmwf-projects/cads-contents-json.git",
                "branch": "prod",
            }
        ],
        "cads-configuration": [
            {
                "url": "https://github.com/ecmwf-projects/cads-configuration",
                "branch": "main",
            },
        ],
    }
    assert effective_conf == expected_conf

    filtering_kwargs = dict()
    for filter_name, repo_category in [
        ("exclude_licences", "cads-licences"),
        ("exclude_messages", "cads-messages"),
        ("exclude_contents", "cads-contents-json"),
    ]:
        filtering_kwargs[filter_name] = True
        del expected_conf[repo_category]
        effective_conf = repos.parse_repos_config(test_config_path, filtering_kwargs)
        assert effective_conf == expected_conf
    filtering_kwargs["exclude_resources"] = True
    del expected_conf["cads-forms-json"]
    del expected_conf["cads-forms-cim-json"]
    effective_conf = repos.parse_repos_config(test_config_path, filtering_kwargs)
    assert effective_conf == expected_conf


class FakeBranch:
    def __init__(self, name):
        self.name = name


class FakeGitRepo:
    def __init__(self, repo_path, branch="main", **kwargs):
        self.branch = branch

    def clone_from(self, repo_url, repo_path, multi_options):
        branch_name = "main"
        for opt in multi_options:
            if "--branch" in opt:
                branch_name = opt.split("--branch")[1].strip()
        return self.__class__.__init__(repo_path, branch_name)

    def delete_remote(self, *args, **kwargs):
        pass

    def remote(self, *args, **kwargs):
        pass

    @property
    def active_branch(self):
        return FakeBranch(self.branch)
