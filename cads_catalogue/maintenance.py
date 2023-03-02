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

import sqlalchemy.engine
import structlog

logger = structlog.get_logger(__name__)


def force_vacuum(
    conn: sqlalchemy.engine.Connection, only_older_than_days: int | None = None
) -> None:
    """
    Force run 'vacuum analyze' on all tables.

    If `only_older_than_days` is not None, running only over tables whose vacuum has not run
    for more than `only_older_than_days` days.

    Parameters
    ----------
    conn: sqlalchemy db connection object
    only_older_than_days: number of days from the last run of autovacuum that triggers the vacuum of the table
    """
    if only_older_than_days is None:
        sql = "SELECT relname FROM pg_stat_all_tables WHERE schemaname = 'public'"
    else:
        days = int(only_older_than_days)
        sql = """
        SELECT relname FROM pg_stat_all_tables
        WHERE schemaname = 'public'
        AND (
         (last_analyze is NULL AND last_autoanalyze is NULL)
          OR (
             (last_analyze < last_autoanalyze OR last_analyze is null)
             AND last_autoanalyze < now() - interval '%s day'
             )
          OR (
             (last_autoanalyze < last_analyze OR last_autoanalyze is null)
             AND last_analyze < now() - interval '%s day'
             )
        )""" % (
            days,
            days,
        )
    tables = conn.execute(sql).scalars()
    for table in tables:
        logger.debug("running VACUUM ANALYZE for table %s" % table)
        vacuum_sql = "VACUUM ANALYZE %s" % table
        conn.execute(vacuum_sql)
