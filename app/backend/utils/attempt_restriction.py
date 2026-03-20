from app_factory import redis_client
from backend.utils.misc import get_ip_address


class AttemptRestricter:
    def __init__(self, key_prefix: str, max_attempts: int, timeout: int,
                 remember_attempts_for: int = 3600*12):
        """Object made for keeping track of action attempts and restrictions.

        Args:
            key_prefix (str): Prefix that will be used id cache keys like `prefix`_attempts.
            max_attempts (int): Max attempts until the restriction can added.   
            timeout (int): Period of time for which further attempts are restricted
            remember_attempts_for (int, optional): Time for which the attempt count will be cached. Defaults to 43200.
        """
        self.user_ip = get_ip_address()
        self.key_prefix: str = key_prefix
        self.max_attempts: int = max_attempts
        self.restriction_timeout: int = timeout
        self.attempts_timeout: int = remember_attempts_for
    
    def is_restricted(self) -> bool:
        """Check if the IP address is restricted. Returns `True`/`False`."""
        return redis_client.get(f'{self.key_prefix}_restricted:{self.user_ip}') is not None
        
    def increase_attempt_count(self):
        """Increase the number of action attempts made. Set it to `1` if it is the first one."""
        try:
            self.action_attempts = redis_client.incr(f'{self.key_prefix}_attempts:{self.user_ip}', 1)
            
        except ValueError:
            redis_client.set(f'{self.key_prefix}_attempts:{self.user_ip}', 1, self.attempts_timeout)
            self.action_attempts = 1
            
        return self.action_attempts
        
    def add_restriction_if_needed(self) -> bool:
        """If the attempt count is bigger than the max attempt number, adds the restriction
        and returns `True`. Does nothing and returns `False` otherwise."""
        if self.action_attempts % self.max_attempts == 0:
            redis_client.set(f'{self.key_prefix}_restricted:{self.user_ip}', 1, self.restriction_timeout)
            return True
        return False
    
    def reset_attempt_count(self):
        redis_client.delete(f'{self.key_prefix}_attempts:{self.user_ip}')
    
    def manually_remove_restriction(self):
        redis_client.delete(f'{self.key_prefix}_restricted:{self.user_ip}')
