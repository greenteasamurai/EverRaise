from redis import Redis
from rq import Queue
from app.core.config import settings
import os

# Initialize Redis connection from settings
# RQ requires a Redis connection object, not just the URL string
redis_conn = Redis.from_url(str(settings.REDIS_URL))

# Define the default RQ queue
# You can define multiple queues (e.g., 'high', 'default', 'low') if needed
# The name 'default' is conventional
queue = Queue(name="default", connection=redis_conn)

# Example for a high-priority queue (if needed)
# high_priority_queue = Queue(name="high", connection=redis_conn)

# Function to check worker count (optional utility)
def get_worker_count(queue_name: str = "default") -> int:
    """Returns the number of workers processing the specified queue."""
    q = Queue(name=queue_name, connection=redis_conn)
    return q.count # This might only show jobs, need to check RQ docs for active worker count 