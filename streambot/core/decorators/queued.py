import asyncio
from functools import wraps

# ------------------------
# Signal hub
# ------------------------
class _SignalHub:
    def __init__(self):
        self.signals = {}  # id -> list of futures

    async def wait(self, signal_id, timeout=None):
        if not signal_id:
            return None
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self.signals.setdefault(signal_id, []).append(fut)
        if timeout is not None:
            return await asyncio.wait_for(fut, timeout)
        return await fut

    def done(self, signal_id, value=None):
        if not signal_id:
            return
        futures = self.signals.pop(signal_id, [])
        for fut in futures:
            if not fut.done():
                fut.set_result(value)

    def cancel(self, signal_id):
        if not signal_id:
            return
        futures = self.signals.pop(signal_id, [])
        for fut in futures:
            if not fut.done():
                fut.cancel()

# ------------------------
# Global queued signals
# ------------------------
class Queued:
    _registry = []

    def __init__(self):
        self._signals = _SignalHub()
        Queued._instance = self

    async def wait(self, signal_id, timeout=None):
        return await self._signals.wait(signal_id, timeout)

    def done(self, signal_id, value=None):
        self._signals.done(signal_id, value)
        # propagate to all decorated function signals
        for wrapper in Queued._registry:
            if hasattr(wrapper, "done"):
                wrapper.done(signal_id, value)

    def cancel(self, signal_id):
        self._signals.cancel(signal_id)


Queued = Queued()

# ------------------------
# queued decorator
# ------------------------
def queued(_func=None, *, maxsize=0, timeout=None):
    def decorator(func):
        wrapper_registry = {}

        async def worker(wrapper_key):
            state = wrapper_registry[wrapper_key]
            q = state["queue"]
            while True:
                try:
                    args, kwargs = await q.get()
                    state["active"] += 1
                    try:
                        if timeout is not None:
                            await asyncio.wait_for(func(*args, **kwargs), timeout)
                        else:
                            await func(*args, **kwargs)
                    except asyncio.TimeoutError:
                        print(f"[queued] Task timed out")
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        print(f"[queued] Task exception: {e}")
                    finally:
                        state["active"] -= 1
                        q.task_done()
                except Exception as e:
                    print(f"[queued] Worker caught exception: {e}")

                # Queue empty hook safely
                try:
                    if q.empty() and state["active"] == 0:
                        cb = getattr(func, f"on_{func.__name__}_empty", None)
                        if cb:
                            if asyncio.iscoroutinefunction(cb):
                                asyncio.create_task(cb())
                            else:
                                cb()
                except Exception as e:
                    print(f"[queued] Queue-empty hook error: {e}")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if wrapper not in wrapper_registry:
                wrapper_registry[wrapper] = {
                    "queue": asyncio.Queue(maxsize=maxsize),
                    "signals": _SignalHub(),
                    "active": 0,
                    "worker": asyncio.create_task(worker(wrapper))
                }
                Queued._registry.append(wrapper)

            state = wrapper_registry[wrapper]
            await state["queue"].put((args, kwargs))

        # ------------------------
        # Function-scoped helpers
        # ------------------------
        async def wait(signal_id, timeout=None):
            if not signal_id:
                return None
            state = wrapper_registry[wrapper]
            return await state["signals"].wait(signal_id, timeout)

        def done(signal_id, value=None):
            if not signal_id:
                return
            state = wrapper_registry[wrapper]
            state["signals"].done(signal_id, value)

        def cancel(signal_id=None):
            state = wrapper_registry[wrapper]
            if signal_id:
                state["signals"].cancel(signal_id)

        def queue_size():
            state = wrapper_registry[wrapper]
            return state["queue"].qsize()

        def is_last():
            state = wrapper_registry[wrapper]
            return state["queue"].qsize() == 0 and state["active"] == 1

        def current_id():
            state = wrapper_registry[wrapper]
            return 1 if state["active"] > 0 else 0

        # Attach helpers
        wrapper.wait = wait
        wrapper.done = done
        wrapper.cancel = cancel
        wrapper.queue_size = queue_size
        wrapper.is_last = is_last
        wrapper.current_id = current_id
        wrapper._registry = wrapper_registry

        return wrapper

    if _func is None:
        return decorator
    return decorator(_func)