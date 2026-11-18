# HighErrorRate

1. Check whether errors started right after a deploy; if so, roll back first.
2. Look at dependency errors in logs (database, queue, upstream timeouts).
3. Check saturation: CPU throttling, memory near limit, connection pool exhaustion.
4. If one pod is the source, cordon and restart it; otherwise scale out.
