import os
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from asgiref.sync import AsyncToSync
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_connection_retry_on_startup = True

app.autodiscover_tasks()


# _P = ParamSpec("_P")
# _R = TypeVar("_R")


def async_task(*args: Any, **kwargs: Any):
    def _decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        sync_call = AsyncToSync(func, force_new_loop=True)

        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*args, **kwargs):
            return sync_call(*args, **kwargs)

        return _decorated

    return _decorator
