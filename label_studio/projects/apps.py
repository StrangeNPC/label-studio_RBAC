from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ProjectsConfig(AppConfig):
    name = 'projects'

    def ready(self):
        logger.info("RBAC: ProjectsConfig.ready() called - importing permissions module")
        from . import permissions
        logger.info("RBAC: ProjectsConfig.ready() completed - permissions module imported")
