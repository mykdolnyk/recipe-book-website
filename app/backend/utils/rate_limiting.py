from flask import abort, Blueprint
import config
from backend.utils.misc import get_ip_address


def setup_rate_limiting(app: Blueprint, redis_client, testing=False):
    if not config.RATE_LIMIT_ENABLED:
        return None

    if app._got_registered_once and testing:
        # Pytest calls this function for every test, and the blueprints 
        # do not reset between tests. So, this block is required
        # to prevent the changes after the BP is registered
        return None
    
    @app.before_request
    def rate_limit():
        ip = get_ip_address()
        key = f'request_count:{ip}'
        
        request_count = redis_client.incr(key)

        if request_count == 1:
            redis_client.expire(key, config.RATE_LIMIT_COOLDOWN)

        elif request_count > config.RATE_LIMIT_MAX_REQUESTS:
            abort(429)

