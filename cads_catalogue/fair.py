"""FAIR related functionalities."""

# Copyright 2025, European Union.
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
import os

import requests
import sqlalchemy as sa
import structlog
from cads_common import portal

from cads_catalogue import database

FAIR_CHEKER_USERNAME = os.getenv("FAIR_CHECKER_USERNAME", "marvel")
FAIR_CHEKER_PASSWORD = os.getenv("FAIR_CHECKER_PASSWORD", "wonderwoman")

logger = structlog.get_logger(__name__)


def call_fair_checker(fair_checker_host: str, site_base: str, dataset_uid: str) -> dict:
    """Check if the FAIR checker service is reachable.

    Args:
        fair_checker_host: Hostname (with port, optionally) of the FAIR checker service.
        site_base: Base URL for DSS portal.
        dataset_uid: Dataset unique identifier.

    Returns:        JSON response from the FAIR checker service.
    """
    payload = {
        "object_identifier": f"{site_base}/datasets/{dataset_uid}",
        "metadata_service_endpoint": "",
        "metadata_service_type": "oai_pmh",
        "use_datacite": True,
        "use_github": False,
        "metric_version": "metrics_v0.8",
    }

    logger.info("Retrieving FAIR report for resource", dataset_uid=dataset_uid)
    response = requests.post(
        f"http://{fair_checker_host}/fuji/api/v1/evaluate",
        headers={
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=payload,
        auth=(FAIR_CHEKER_USERNAME, FAIR_CHEKER_PASSWORD),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def update_fair_score(session: sa.orm.Session, fair_checker_host: str) -> None:
    """Update the FAIR score for all resources in the catalogue.

    Args:
        session_obj: SQLAlchemy session object.
        fair_checker_service_url: URL of the FAIR checker service.
    """
    resources = session.query(database.Resource).all()
    for resource in resources:
        site_base = portal.get_site_url(resource.portal) if resource.portal else None
        if not site_base:
            logger.warning(
                "Cannot determine site base URL for portal",
                portal=resource.portal,
                resource_id=resource.resource_uid,
            )
            continue
        dataset_uid = resource.resource_uid
        assert dataset_uid is not None
        try:
            result = call_fair_checker(fair_checker_host, site_base, dataset_uid)
        except requests.RequestException as e:
            logger.error(
                "Error connecting to FAIR checker service",
                error=str(e),
                resource_id=resource.resource_uid,
            )
            continue
        resource.fair_timestamp = datetime.datetime.utcnow()
        try:
            session.execute(
                sa.update(database.ResourceData)
                .where(database.ResourceData.resource_uid == resource.resource_uid)
                .values(fair_data=result),
            )
            session.add(resource)
            session.commit()
        except sa.exc.SQLAlchemyError as e:
            session.rollback()
            logger.error(
                "Error updating FAIR data",
                error=str(e),
                resource_id=resource.resource_uid,
            )
            continue
        logger.info("Updated FAIR data", resource_id=resource.resource_uid)
