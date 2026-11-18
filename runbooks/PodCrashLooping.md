# PodCrashLooping

1. `kubectl describe pod` and look at the last state: OOMKilled, Error, or probe failure.
2. OOMKilled: compare memory to the limit and look for a leak or a limit set too low.
3. Probe failure: check startup time against the probe's initial delay.
4. Error exit: read the previous container's logs (`kubectl logs --previous`).
