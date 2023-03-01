"""utilities for faceted search."""

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

from typing import List, Tuple

from sqlalchemy.orm.session import Session

from cads_catalogue import database

"""
usage example:

from cads_catalogue import database
from cads_catalogue.faceted_search import get_datasets_by_keywords, get_faceted_stats

session_obj = database.ensure_session_obj()
session = session_obj()

# consider all the datasets (but you can start with a filtered set of resources,
# for example a result of a text search on the title)
datasets = session.query(database.Resource).all()

# Build keywords_dict: a dictionary where keys are the selected categories
# and the values are the lists of the values selected for the corresponding category.
# For example, selecting
#  "Product type" -> "Reanalysis"
#  "Product type" -> "Reactive gas"
#  "Variable domain" -> "Atmosphere (composition)"
keywords_dict = {"Product type": ["Reanalysis", "Reactive gas"],
                 "Variable domain": ["Atmosphere (composition)"]}

# Obtain list of datasets that are the results of the query:
dataset_results = get_datasets_by_keywords(datasets, keywords_dict)

# the corresponding faceted stats are something like:
#  [('Parameter family', 'Aerosol', 2), ('Parameter family', 'Reactive gas', 3), ...]
# and can be obtained passing the ids of the dataset_results to the get_faceted_stats:
results_ids = [d.resource_id for d in dataset_results]
faceted_stats = get_faceted_stats(session, results_ids)
"""


def get_faceted_stats(
    session: Session, resource_ids: List[int]
) -> List[Tuple[str, str, int]]:
    """
    Return list of (category_name, category_value, number of datasets).

    Parameters
    ----------
    session: opened SQLAlchemy session
    resource_ids: input resource ids

    Returns
    -------
    Something like: [('Parameter family', 'Aerosol', 2), ('Parameter family', 'Reactive gas', 3), ...]
    """
    # FIXME: replace using sqlalchemy, not SQL
    sql = """
    SELECT category_name, category_value, count(resource_id)
    FROM resources_keywords
    LEFT JOIN keywords USING (keyword_id)
    WHERE resource_id in (%s)
    GROUP BY (category_name, category_value)
    ORDER BY category_name, category_value
    """ % ",".join(
        ["%s" % r for r in resource_ids]
    )
    result = session.execute(sql).all()
    return result  # type: ignore


def get_datasets_by_keywords(
    resources: List[database.Resource], keywords_dict: dict[str, List[str]]
) -> List[int]:
    """
    Return the list of resources matching to a set of input keywords.

    keywords_dict is a dictionary of kind:
    {cat_name1: [value11, value12, value13, ...], cat_name2: [value21, value22, value23, ...], ....}
    where:
     - "cat_nameX: valueXY" is a keyword
     - each value of the list [valueXY, valueXZ, ...] to be matched in logic OR
     - each key:value of the dict to be matched in logic AND to the others

    Parameters
    ----------
    resources: list of resource objects
    keywords_dict: dictionary of keywords' query

    Returns
    -------
    List of resources
    """
    resources_set = set(resources)
    for cat_name, values in keywords_dict.items():
        category_datasets = set()
        for value in values:
            keyword = "%s: %s" % (cat_name, value)
            for resource in resources_set:
                if keyword in [k.keyword_name for k in resource.keywords]:  # type: ignore
                    category_datasets.add(resource)
        resources_set = resources_set.intersection(category_datasets)
    return list(resources_set)  # type: ignore
