# Copyright 2016-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import os
import shutil

from odoo import http
from odoo.tools import config
from odoo.tools.func import lazy_property

from .session import RedisSessionStore
from .strtobool import strtobool

_logger = logging.getLogger(__name__)

try:
    import redis
    from redis.sentinel import Sentinel
except ImportError:
    redis = None  # noqa
    _logger.debug("Cannot 'import redis'.")


def is_true(strval):
    _logger.debug("is trueee? %s",bool(strtobool(strval or "0".lower())))
    return bool(strtobool(strval or "0".lower()))


config_option = config.options


# # if gets from env
# sentinel_host = os.environ.get("ODOO_SESSION_REDIS_SENTINEL_HOST")
# sentinel_master_name = os.environ.get("ODOO_SESSION_REDIS_SENTINEL_MASTER_NAME")

sentinel_host = config_option.get("session_redis_sentinel_host")
sentinel_master_name = config_option.get("session_redis_sentinel_master_name")

if sentinel_host and not sentinel_master_name:
    raise Exception(
        "ODOO_SESSION_REDIS_SENTINEL_MASTER_NAME must be defined "
        "when using session_redis"
    )
    
# # if gets from env
# sentinel_port = int(os.environ.get("ODOO_SESSION_REDIS_SENTINEL_PORT", 26379))
# host = os.environ.get("ODOO_SESSION_REDIS_HOST", "localhost")
# port = int(os.environ.get("ODOO_SESSION_REDIS_PORT", 6379))
# prefix = os.environ.get("ODOO_SESSION_REDIS_PREFIX")
# url = os.environ.get("ODOO_SESSION_REDIS_URL")
# password = os.environ.get("ODOO_SESSION_REDIS_PASSWORD")
# expiration = os.environ.get("ODOO_SESSION_REDIS_EXPIRATION")
# anon_expiration = os.environ.get("ODOO_SESSION_REDIS_EXPIRATION_ANONYMOUS")


sentinel_port = int(config_option.get("session_redis_sentinel_port", 26379))
host = config_option.get("session_redis_host", "localhost")
port = int(config_option.get("session_redis_port", 6379))
prefix = config_option.get("session_redis_prefix")
url = config_option.get("session_redis_url")
password = config_option.get("session_redis_password")
expiration = config_option.get("session_redis_expiration")
anon_expiration = config_option.get("session_redis_expiration_anonymous")



@lazy_property
def session_store(self):
    _logger.debug("session_store function trigered")

    if sentinel_host:
        sentinel = Sentinel([(sentinel_host, sentinel_port)], password=password)
        redis_client = sentinel.master_for(sentinel_master_name)
    elif url:
        redis_client = redis.from_url(url)
    else:
        redis_client = redis.Redis(host=host, port=port, password=password)
    return RedisSessionStore(
        redis=redis_client,
        prefix=prefix,
        expiration=expiration,
        anon_expiration=anon_expiration,
        session_class=http.Session,
    )


def purge_fs_sessions(path):
    # for fname in os.listdir(path):
    #     path = os.path.join(path, fname)
    #     try:
    #         os.unlink(path)
    #     except OSError:
    #         _logger.warning("OS Error during purge of redis sessions.")
        _logger.debug(f"Attempting to purge sessions in directory: {path}")

        for fname in os.listdir(path):
            file_path = os.path.join(path, fname)
            try:
                if os.path.isfile(file_path):
                    try:
                        os.unlink(file_path)
                        _logger.debug("Successfully deleted session file: %s", file_path)
                    except FileNotFoundError:
                        _logger.warning(f"File not found during purge of redis sessions: {file_path}")
                    except PermissionError:
                        _logger.warning(f"Permission error during purge of redis sessions file: {file_path}")
                    except OSError as e:
                        _logger.warning(f"OS Error during purge of redis sessions file : {e}")
                else:
                    try:
                        shutil.rmtree(file_path)
                        _logger.debug("Successfully deleted session directory: %s", file_path)
                    except FileNotFoundError:
                        _logger.warning(f"directory not found during purge of redis sessions: {file_path}")
                    except PermissionError:
                        _logger.warning(f"Permission error during purge of redis sessions directory: {file_path}")
                    except OSError as e:
                        _logger.warning(f"OS Error during purge of redis sessions in directory: {e}")
    
            except OSError as e:
                        _logger.warning(f"OS Error during purge of redis sessions: {e}")

# if is_true(os.environ.get("ODOO_SESSION_REDIS")): # if gets from env
if is_true(config_option.get("session_redis")):
    _logger.debug("SESSION_REDIS is activated sentinel_host %s,host %s,port %s,prefix %s,url %s,password %s,expiration %s,anon_expiration %s ",sentinel_host,host,port,prefix,url,password,expiration,anon_expiration)
    _logger.debug("config_option: %s", config_option)
    
    if sentinel_host:
        _logger.debug(
            "HTTP sessions stored in Redis with prefix '%s'. "
            "Using Sentinel on %s:%s",
            prefix or "",
            sentinel_host,
            sentinel_port,
        )
    else:
        _logger.debug(
            "HTTP sessions stored in Redis with prefix '%s' on " "%s:%s",
            prefix or "",
            host,
            port,
        )
    
    http.Application.session_store = session_store
    # clean the existing sessions on the file system
    purge_fs_sessions(config.session_dir)