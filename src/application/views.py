from flask_cache import Cache

from application import app


# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)


def warmup():
    """App Engine warmup handler
    """
    return ''
