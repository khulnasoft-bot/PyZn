import csv
import datetime
import timeit
from logging import Logger
from typing import Iterable, List, Generator

import attr
from commandbus import Command, CommandHandler

from pyzn.application.admin_password_checker import AdminPasswordChecker
from pyzn.domain.exception import InvalidAdminPassword
from pyzn.domain.model import Project, Password, Downloads, ProjectName, DayDownloads
from pyzn.domain.pypi import StatsViewer, Row
from pyzn.domain.repository import ProjectRepository


@attr.s()
class ImportTotalDownloadsRow:
    project: str = attr.ib()
    total_downloads: int = attr.ib()


class ImportTotalDownloads(Command):
    def __init__(self, file_path: str):
        self.file_path = file_path


class ImportTotalDownloadsHandler(CommandHandler):
    def __init__(self, project_repository: ProjectRepository, logger: Logger):
        self._project_repository = project_repository
        self._logger = logger

    def handle(self, cmd: ImportTotalDownloads):
        for batch_iterator, batch in enumerate(self._batch(cmd.file_path, 250), start=1):
            self._logger.info(f"Batch {batch_iterator}")
            projects = {}
            for row in batch:
                if row.project in projects:
                    project = projects.get(row.project)
                else:
                    project = self._project_repository.get(row.project)
                if project is None:
                    project = Project(ProjectName(row.project), Downloads(0))
                project.total_downloads = Downloads(row.total_downloads)
                projects[row.project] = project
            self._project_repository.save_projects(list(projects.values()))

    def _batch(self, file_path: str, batch_size: int) -> Generator[List[ImportTotalDownloadsRow], None, None]:
        self._logger.info("Importing total downloads file from " + file_path)
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            data = []
            for r in reader:
                data.append(ImportTotalDownloadsRow(r["project"], int(r["total_downloads"])))
                if len(data) == batch_size:
                    yield data
                    data = []
            yield data


class UpdateVersionDownloads(Command):
    def __init__(self, date: datetime.date):
        self.date = date


class UpdateVersionDownloadsHandler(CommandHandler):
    def __init__(
        self,
        project_repository: ProjectRepository,
        stats_viewer: StatsViewer,
        admin_password_checker: AdminPasswordChecker,
        logger: Logger,
    ):
        self._project_repository = project_repository
        self._stats_viewer = stats_viewer
        self._admin_password_checker = admin_password_checker
        self._logger = logger

    def handle(self, cmd: UpdateVersionDownloads):
        self._logger.info(f"Getting downloads from date {cmd.date}...")
        stats_result = self._stats_viewer.get_version_downloads(cmd.date)
        self._logger.info(f"Retrieved {stats_result.total_rows} downloads. Saving to db...")
        start_time = timeit.default_timer()
        total_batches = int(stats_result.total_rows / 250)
        for batch_iterator, batch in enumerate(self._batch(stats_result.rows, 250)):
            self._logger.info(f"Batch {batch_iterator} of {total_batches}")
            projects = {}
            for row in batch:
                if row.project in projects:
                    project = projects.get(row.project)
                else:
                    project = self._project_repository.get(row.project, downloads_from=cmd.date)
                if project is None:
                    project = Project(ProjectName(row.project), Downloads(0))
                project.add_downloads(row.date, row.version, DayDownloads(row.downloads, row.pip_downloads))
                projects[row.project] = project
            self._project_repository.save_projects(list(projects.values()))
        end_time = timeit.default_timer()
        self._logger.info(f"Total downloads updated. Total time + {(end_time - start_time):.4f} seconds")

    def _batch(self, rows: Iterable[Row], batch_size: int) -> Generator[List[Row], None, None]:
        data = []
        for r in rows:
            data.append(r)
            if len(data) == batch_size:
                yield data
                data = []
        yield data
