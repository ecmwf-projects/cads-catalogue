"""sanity-check-related functionalities and dependencies."""

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

from __future__ import annotations

import datetime
import json
import os
from collections import defaultdict
from operator import itemgetter
from typing import Any, Dict, List

import jsonschema
import sqlalchemy as sa
import structlog
import typer

from cads_catalogue import database, utils

logger = structlog.get_logger(__name__)

try:
    import cads_e2e_tests  # type: ignore
except ImportError:
    #  cads-e2e-tests not wanted in retrieve-api, it cannot process sanity checks
    pass

SCHEMA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "schemas")

format_checking = jsonschema.FormatChecker(formats=["date", "date-time", "uuid"])

ref_mapping = {}
for schema_def in ("sanity_check", "sanity_check_item"):
    with open(os.path.join(SCHEMA_PATH, f"{schema_def}.json")) as fp:
        ref_mapping[f"/schemas/{schema_def}"] = json.load(fp)

SanityCheckValidator = jsonschema.validators.validator_for(
    ref_mapping["/schemas/sanity_check"]
)
SanityCheckItemValidator = jsonschema.validators.validator_for(
    ref_mapping["/schemas/sanity_check_item"]
)

sanity_check_validator = SanityCheckValidator(
    schema=ref_mapping["/schemas/sanity_check"],
    resolver=jsonschema.RefResolver("", {}, store=ref_mapping),
    format_checker=format_checking,
)
sanity_check_item_validator = SanityCheckItemValidator(
    schema=ref_mapping["/schemas/sanity_check_item"],
    resolver=jsonschema.RefResolver("", {}, store=ref_mapping),
    format_checker=format_checking,
)


def echo_passed_vs_failed(reports: list[cads_e2e_tests.Report]) -> None:
    """Print some statistics about reports."""
    n_reports = len(reports)
    typer.secho(
        f"NUMBER OF REPORTS: {n_reports}",
        fg=typer.colors.YELLOW if not n_reports else None,
    )
    if n_reports:
        failed = sum(True for request in reports if request.tracebacks)
        passed = len(reports) - failed
        failed_perc = failed * 100 / n_reports
        passed_perc = passed * 100 / n_reports
        if failed:
            typer.secho(f"FAILED: {failed} ({failed_perc:.1f}%)", fg=typer.colors.RED)
        if passed:
            typer.secho(f"PASSED: {passed} ({passed_perc:.1f}%)", fg=typer.colors.GREEN)


def sanitize_datetimes(sanity_check):
    """Return a sanity_check item with iso dates with timezone."""
    # in the long run this function will become legacy
    ret_value = sanity_check.copy()
    for key in ("started_at", "finished_at"):
        time_obj = datetime.datetime.fromisoformat(sanity_check[key])
        if time_obj.tzinfo is None:
            ret_value[key] = time_obj.replace(tzinfo=datetime.timezone.utc).isoformat()
    return ret_value


def report2sanity_check(report: cads_e2e_tests.Report) -> dict[str, Any]:
    """Return a sanity check information from a cads-e2e-tests's report."""
    sanity_check = {
        "req_id": report.request_uid,
        "success": not report.tracebacks,
        "started_at": report.started_at.isoformat(),
        "finished_at": report.finished_at.isoformat(),
    }
    sanity_check = sanitize_datetimes(sanity_check)
    sanity_check_item_validator.validate(sanity_check)
    return sanity_check


def update_dataset_sanity_check(
    session_obj: sa.orm.sessionmaker,
    dataset_uid: str,
    report: cads_e2e_tests.Report,
    retain_only: int,
) -> None:
    """Update sanity check column with a new outcome."""
    current_sanity_check = report2sanity_check(report)
    with session_obj.begin() as session:
        dataset_obj = session.scalars(
            sa.select(database.Resource).filter_by(resource_uid=dataset_uid)
        ).first()
        if not dataset_obj:
            logger.error(
                f"dataset uid {dataset_uid!r} in sanity check report was "
                f"not found in the catalogue database!"
            )
            return
        old_sanity_check = dataset_obj.sanity_check or []
        new_sanity_check = [sanitize_datetimes(s) for s in old_sanity_check] + [
            current_sanity_check
        ]
        # note: sorting works with string if datetimes use isoformat!
        new_sanity_check = sorted(
            new_sanity_check, key=itemgetter("started_at"), reverse=True
        )
        if retain_only > 0:
            new_sanity_check = new_sanity_check[:retain_only]
        sanity_check_validator.validate(new_sanity_check)
        dataset_obj.sanity_check = new_sanity_check
        session.add(dataset_obj)
    logger.info(f"sanity check information updated for {dataset_uid!r}.")


def update_sanity_checks_by_file(
    session_obj: sa.orm.sessionmaker, report_path: str, retain_only: int
):
    """Update all sanity check columns by a reports file."""
    with open(report_path) as fp:
        reports = cads_e2e_tests.load_reports(fp)
    dashboard_dict: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for report in reports:
        dashboard_dict[report.request.collection_id].append(report2sanity_check(report))
    with session_obj.begin() as session:
        all_datasets = session.scalars(sa.select(database.Resource)).all()
        for dataset in all_datasets:
            if dataset.resource_uid in dashboard_dict:
                additional_sanity_checks = dashboard_dict.pop(dataset.resource_uid)
                old_sanity_check = dataset.sanity_check or []
                new_sanity_check = old_sanity_check + additional_sanity_checks
                new_sanity_check = utils.sorted_by_isoformats(
                    new_sanity_check, time_key="started_at", reverse=True
                )
                if retain_only > 0:
                    new_sanity_check = new_sanity_check[:retain_only]
                dataset.sanity_check = new_sanity_check
                session.add(dataset)
            else:
                logger.warning(
                    f"dataset {dataset.resource_uid} not included in this sanity check report"
                )
    for dataset_uid in dashboard_dict:
        logger.error(
            f"dataset uid {dataset_uid!r} in sanity check report was "
            f"not found in the catalogue database!"
        )


def run_sanity_check(session_obj: sa.orm.sessionmaker, retain_only: int, **kwargs):
    """Run e2e sanity checks and store outcomes."""
    requests_path: str | None = kwargs.pop("requests_path", None)
    if requests_path is not None:
        with open(requests_path, "r") as fp:
            kwargs["requests"] = cads_e2e_tests.load_requests(fp)
    else:
        kwargs["requests"] = None
    reports = []
    for report in cads_e2e_tests.reports_generator(**kwargs):
        reports.append(report)
        dataset_uid = report.request.collection_id
        if not dataset_uid:
            continue
        try:
            update_dataset_sanity_check(session_obj, dataset_uid, report, retain_only)
        except Exception:  # noqa
            logger.exception(
                f"sanity check outcome not stored for {dataset_uid!r}, error follows"
            )
            continue
    echo_passed_vs_failed(reports)
