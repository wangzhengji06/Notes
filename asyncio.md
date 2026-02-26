## 1. Getting to know asyncio

Concurrent IO: Allow multiple web requests to be made at the same time.

CPU-bound vs IO-bound: Limited by clock speed of CPU or I/O device handling speed.

CPU-bound: computation, iteration etc....

IO-bound: read, write, download...

### Concurrency, Parallelism, Multitasking

Concurrency: Switching between tasks (Baking two cakes with one oven)

Parallelism: Tasks really running at the same time (Baking two cakes with two ovens)

Multitasking: copperative mulitasking, expicitly deicde code points in which other tasks can be run

### Process, thread, multithread, multiprocess

Process: an application run that has a memory space that other applications cannot access.

A machine with single cpu can still run mulitple processes, with time slicing.

Thread: Light-weight process, share the memory of the process that created them.

Both processes and threads can be concurrent and parallel.

Multithread is good for IO-bound task while multiprocess is good for cpu-heavy task.

### Global Interpreter Lock

GIL prevents one Python process from executing more than one Python bytecode.

This means that, even if we have multiple threads, a python process can have only one thread running python codes at a time.

This causes a problem to multithread, but not multiprocess because each process has its own GIL.

Why? Because Cpython uses a process called "reference counting" for garbage collection.

GIL conflicts with python When multiple threads read and write, that can put the state in an unexpected condition.

Therefore, even when you use multithreads, the GIL will block one threads when another is running, this basically negate the values of multithreading.

### The value of multithreading

Even though it is not suitable for CPU-bound, it is great for IO_bound, because GIL only happens when data recieved is translated into a Python Object.

asyncio create objects called coroutines. A coroutine can be thought of as excuting a lightweight thread. asyncio uses coroutines to make sure that when one operation is waiting, others can do something else.

### Single-Threaded Concurrency

Socket: low-level abstraction for sending and receiving data over a network.

By default, socket works in blocking mode, which means when we are waiting that server sends back byte so that application can read it, the application's operations got stopped.

At the operating system level, we do not need to do this blocking. We can do other things after data is written to socket, and system is going to tell use when we recieve bytes.

In asyncio's model of concurrency, one thread is executing Python at given time. When we hit I/O operation, we hand it over to Operating system.

### Event Loop: How we keep track of which tasks are waiting for I/O

In asyncio, the event loop keeps a queue of tasks instead of messages. If a task hits an I/O oepration, it will be paused and next task will be runned. For the next iteration, the I/O will be checked whether it has completed.

## 2. asyncio basics

### What is coroutine?

Think of it as a regular Python function that can pauses its execution when encounter operation that can take a while to finish.

The only syntax difference is we use async def intead of def.

Coroutine aren't executed when being called directly. To run it, we need to explicitly run it on an event loop.

A convenient way to do it is to use "asyncio.run()". This is supposes to be the entry point of a coroutine that starts all the other coroutines also.

async creates a coroutine object, while await object allows the object in whcih the coroutine it contained to be paused if it requires waiting, the control would be handed to event loop.

This concept is very important.

### Long-runing coroutine with sleep

asyncio.sleep itself is a coroutine.

it is noticebale that, await pauses current coroutine and won't execute any other code inside that coroutine until the await expression gives us a value.

### Run concurrently with tasks

To run anything concurrently, we need to use task.

If you create a task, you give a coroutine to the event loop, and you can put it after await.

The task will not run, but you basically saies, if it hit awaits, please run something else at the same time according to event loop.

Mindset:

Main coroutine runs → creates tasks → hits await → main pauses → event loop schedules runnable tasks → tasks run until they hit await → event loop switches → once the awaited task finishes and control returns to the loop, main resumes.

### Cancel tasks and set timeouts

We can use task.cancel() to change a task to cancelled state. The task.done() will return True, and await task will raise CancelledError.

Also, wait_for(task, timeout=1) would automatically cancel the task and raise a TimedoutError.

wait_fot(asyncio.shield(task), timeout=1) woulld still throw TimedoutError, but the task would not be cancelled.

### Tasks, coroutines, futures and awaitables

Future represents an object that will get value in the future but not yet. it has done() state, and once it is completed, .result() will return the value. set_future() can be used to set value for it.

if we await future, it means, "pause until the future has a value set that can be worked with, and once it had it, wake up and let me process it"

Task directly inherits from future. A task is like a combination of coroutine and future. When task created, we created an empty task and run the coroutine. Once it si finished, we set the result to future.

Coroutine and Future inherits from awaitable, and task inherits from future.

### Measuring coroutine execution time with decorators

Check the code...

### The pitfalls of coroutine and tasks

1. Don't run CPU-bound code in task.
2. Don't block I/O-bound APIs without using multithreading (async used with requests, but actually you should use multithreading).

### Acessing and manually managing the event loop

We can manually create an event loop using `asyncio.new_event_loop`

`loop.call_soon()` will sechdule a function to run on the next iteration of the event loop.

### Debug Mode

`asyncio.run(coroutine(), debug=True)`

## A first asyncio application

### Working with blocking socket

The code below shows a most basic server socket app to listen to connections from client side.

```Python
import socket

# AF_INET means hostname + port will be the format to interact with, SOCK_STREAM means TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow use to reuse the port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)
server_socket.listen()

# This tells our socket to listen for the incoming connections, the oprations will block
connection, client_address = server_socket.accept()
print(f'I got a connection from {client_address}!')
```

### Reading and Writing data to and from a socket

The code below shows a blocking server that can read and write to socket for multiple client connections

However, when a first client get the connection, before it send anything to client, the second client cannot connect.

This is because `accept` and `recv` methods block until they recieve data.

```Python
import socket

# AF_INET means hostname + port will be the format to interact with, SOCK_STREAM means TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow use to reuse the port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)
server_socket.listen()

connections = []


try:
    while True:
        connection, client_address = server_socket.accept()
        print(f'I got a connection from {client_address}!')
        connections.append(connection)
        for connection in connections:
            buffer = b''
            while buffer[-2:] != b'\r\n':
                data = connection.recv(2)
                if not data:
                    break
                else:
                    print(f'I got data: {data}!')
                    buffer = buffer + data
            print(f"All the data is: {buffer}")

            connection.send(buffer)
finally:
     server_socket.close()
```

### Working with non-blocking sockets

A first trail of creating non-blocking sockets by making it nonblocking socket with try and catch when no connection is waiting.

```Python
import socket

# AF_INET means hostname + port will be the format to interact with, SOCK_STREAM means TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow use to reuse the port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.bind(server_address)
server_socket.listen()
server_socket.setblocking(False)

connections = []


try:
    while True:
        try:
            connection, client_address = server_socket.accept()
            print(f'I got a connection from {client_address}!')
            connections.append(connection)
            connection.setblocking(False)
        except BlockingIOError:
            pass

        for connection in connections:
            try:
                buffer = b''
                while buffer[-2:] != b'\r\n':
                    data = connection.recv(2)
                    if not data:
                        break
                    else:
                        print(f'I got data: {data}!')
                        buffer = buffer + data
                print(f"All the data is: {buffer}")
                connection.send(buffer)
            except BlockingIOError:
                pass
finally:
     server_socket.close()


```

### Using the selectors module to build a socket event loop

The previous code will keep cpu at 100%.

But the following code will use very little cpu, because it monitors on a hardware level.

```Python
import selectors
import socket
from selectors import SelectorKey
from typing import List, Tuple

selector = selectors.DefaultSelector()

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ('127.0.0.1', 8000)
server_socket.setblocking(False)
server_socket.bind(server_address)
server_socket.listen()

selector.register(server_socket, selectors.EVENT_READ)

while True:
    events: List[Tuple[SelectorKey, int]] = selector.select(timeout=1)

    if len(events) == 0:
        print("No events, wait a bit more")

    for event, _ in events:
        event_socket = event.fileobj

        if event_socket == server_socket:
            connection, address = server_socket.accept()
            connection.setblocking(False)
            print(f"I got a connection from {address}")
            selector.register(connection, selectors.EVENT_READ)
        else:
            data = event_socket.recv(1024)
            print(f"I got some data: {data}")
            event_socket.send(data)

```

This scenario shares some similarity with asyncio event loop.

Each iteration of event loop is triggered by 1. A socket event happening 2. A timeout is triggered.

For asyncio, it is the same, either the coroutines is completed, or they hit the next await event.

```Python

ready = []      # coroutines ready to run
paused = {}     # coroutine -> what it is waiting for
timers = []     # (wake_time, coroutine)
selector = Selector()

while ready or paused:
    new_ready = []

    # 1. Run all ready coroutines
    for coro in ready:
        try:
            wait = coro.send(None)   # run until next await
        except StopIteration:
            # coroutine finished → remove it permanently
            continue

        # 2. Coroutine yielded control (hit await)
        if wait.type == "SOCKET":
            selector.register(wait.socket)
            paused[coro] = wait

        elif wait.type == "SLEEP":
            timers.append((current_time() + wait.seconds, coro))
            paused[coro] = wait

    ready = []

    # 3. Determine how long we can sleep
    timeout = time_until_next_timer(timers)

    # 4. Wait for socket events or timeout
    events = selector.select(timeout)

    # 5. Wake coroutines waiting on socket events
    for event in events:
        coro = paused.pop(event.coro)
        new_ready.append(coro)

    # 6. Wake coroutines whose timers expired
    for wake_time, coro in expired_timers(timers):
        paused.pop(coro)
        new_ready.append(coro)

    ready = new_ready

```

- An event loop runs continuously and manages the execution of coroutines.

- Coroutines run until they reach an await, at which point they yield control back to the event loop.

- When a coroutine is suspended:
  1.it is paused, not removed 2.the event loop records what it is waiting for (socket readiness or a timer)

- The event loop uses an OS-level selector to efficiently wait for socket events.

- Time-based waits (e.g. asyncio.sleep) are handled using timers, which determine how long the event loop can sleep.

- The event loop sleeps until: 1. a registered socket becomes ready, or 2. the next timer expires

- When a wait condition is satisfied, the corresponding coroutine is moved back to the ready queue.

- Coroutines that finish execution are removed permanently from the event loop.

- Only one coroutine runs at a time; concurrency is achieved through cooperative multitasking via await.

### Using asyncio event loop to ease things up

Using selector might be too low-level in a lot of sutations.

There are three corotuines we want to work with: sock_accept, sock_recv, sock_sendall.

sock_accept: return a tuple of scoket connection and a client address

sock_recv: await until a socket has bytes we can process

sock_sendall: takes in both a socket and data we want to send and wait until the data we want to send to a socket has been sent and will return None on success

```Python
import asyncio
import socket
from asyncio import AbstractEventLoop

async def echo(connection: socket, loop: AbstractEventLoop) -> None:
    while data := await loop.sock_recv(connection, 1024):
        await loop.sock_sendall(connection, data)


async def listen_for_connection(server_socket: socket,
                               loop: AbstractEventLoop):
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"Got a connection from {address}")
        asyncio.create_task(echo(connection, loop))


async def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('127.0.0.1', 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()

    await listen_for_connection(server_socket, asyncio.get_event_loop())

asyncio.run(main())


```

The key idea of choosing betweeing a coroutine and task is:
Use a coroutine when work is sequential and owned by its caller; wrap a coroutine in a task when it needs to run concurrently and independently.

### Handling Error

```Python
import asyncio
import logging
import signal
import socket
from asyncio import AbstractEventLoop
from typing import List

logging.basicConfig(level=logging.INFO)

echo_tasks: List[asyncio.Task] = []


async def echo(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while True:
            data = await loop.sock_recv(connection, 1024)
            if not data:
                break

            print("got data!")

            if data == b"boom\r\n":
                raise Exception("Unexpected network error")

            await loop.sock_sendall(connection, data)

    except Exception as ex:
        # Logs traceback immediately; the exception won't be "lost" inside the task.
        logging.exception("echo failed: %s", ex)

    finally:
        connection.close()


async def connection_listener(server_socket: socket.socket, loop: AbstractEventLoop) -> None:
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"Got a connection from {address}")

        task = asyncio.create_task(echo(connection, loop))
        echo_tasks.append(task)


class GracefulExit(SystemExit):
    pass


def shutdown() -> None:
    raise GracefulExit()


async def close_echo_tasks(tasks: List[asyncio.Task]) -> None:
    # Give each task up to 2 seconds to finish; if it doesn't, cancel it.
    waiters = [asyncio.wait_for(t, timeout=2) for t in tasks]

    for waiter in waiters:
        try:
            await waiter
        except asyncio.TimeoutError:
            # Expected: some echo loops might still be blocked waiting for recv
            pass
        except Exception:
            # If echo() didn't catch/log for some reason, don't crash shutdown
            logging.exception("Task failed during shutdown")

    # Ensure any still-pending tasks are cancelled
    for t in tasks:
        if not t.done():
            t.cancel()

    # Drain cancellations
    await asyncio.gather(*tasks, return_exceptions=True)


async def main(loop: asyncio.AbstractEventLoop) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ("127.0.0.1", 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame), shutdown)

    await connection_listener(server_socket, loop)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(main(loop))
except GracefulExit:
    loop.run_until_complete(close_echo_tasks(echo_tasks))
finally:
    loop.close()
async def echo(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while True:
            data = await loop.sock_recv(connection, 1024)
            if not data:
                break
            print("got data!")
            if data == b"boom\r\n":
                raise Exception("Unexpected network error")
            await loop.sock_sendall(connection, data)

    except Exception as ex:
        # Logs the full traceback immediately, inside the task
        logging.exception("echo task crashed: %s", ex)

    finally:
        connection.close())

```

The tricky part here is that if you just create tasks in a coroutine and that task actually has an error, you will not know that immediately. This is because asyncio.create_task() schedules the coroutine to run independently, and any exception raised inside that task is captured and stored inside the Task object, not propagated to the code that created it.

An exception from a task is only re-raised when the task is awaited (or when its result/exception is explicitly retrieved). If the task is never awaited, the exception does not bubble up to the caller, and asyncio may only report it later—or not at all—depending on garbage collection and program shutdown timing.

As a result, it is better to create a try / except block inside the task itself so that errors are handled or logged at the point where they occur, ensuring failures are visible even when the task is running in the background and is never awaited.

### Shutdown Gracefully

```Python
import asyncio
import logging
import signal
import socket
from asyncio import AbstractEventLoop
from typing import List

logging.basicConfig(level=logging.INFO)

echo_tasks: List[asyncio.Task] = []


async def echo(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while True:
            data = await loop.sock_recv(connection, 1024)
            if not data:
                break

            print("got data!")

            if data == b"boom\r\n":
                raise Exception("Unexpected network error")

            await loop.sock_sendall(connection, data)

    except Exception as ex:
        # Logs traceback immediately; the exception won't be "lost" inside the task.
        logging.exception("echo failed: %s", ex)

    finally:
        connection.close()


async def connection_listener(server_socket: socket.socket, loop: AbstractEventLoop) -> None:
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"Got a connection from {address}")

        task = asyncio.create_task(echo(connection, loop))
        echo_tasks.append(task)


class GracefulExit(SystemExit):
    pass


def shutdown() -> None:
    raise GracefulExit()


async def close_echo_tasks(tasks: List[asyncio.Task]) -> None:
    # Give each task up to 2 seconds to finish; if it doesn't, cancel it.
    waiters = [asyncio.wait_for(t, timeout=2) for t in tasks]

    for waiter in waiters:
        try:
            await waiter
        except asyncio.TimeoutError:
            # Expected: some echo loops might still be blocked waiting for recv
            pass
        except Exception:
            # If echo() didn't catch/log for some reason, don't crash shutdown
            logging.exception("Task failed during shutdown")

    # Ensure any still-pending tasks are cancelled
    for t in tasks:
        if not t.done():
            t.cancel()

    # Drain cancellations
    await asyncio.gather(*tasks, return_exceptions=True)


async def main(loop: asyncio.AbstractEventLoop) -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ("127.0.0.1", 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame), shutdown)

    await connection_listener(server_socket, loop)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    loop.run_until_complete(main(loop))
except GracefulExit:
    loop.run_until_complete(close_echo_tasks(echo_tasks))
finally:
    loop.close()

```

This shutdown gracefully logic is really really hard, I think the best thing to summarize it is: Shutdown must interrupt the main coroutine, not run alongside it.

To clean up the async task by canceling them, while also interrupt the loop,

Also here the reason why we do not use asyncio.run() is because asyncio.run() will aggresively cancel all the tasks after finished(This is like its trait)

## 3. Concurrent Web requests

### Asynchronous context managers

Asynchronous context managers are classes that implement two special coroutine methods, `__aenter__`, and `__aexit__`, which asynchrnously requires and closes the resources.

```Python
import asyncio
import socket
from types import TracebackType
from typing import Optional, Type


class ConnectedSocket:

    def __init__(self, server_socket):
        self._connection = None
        self._server_socket = server_socket

    async def __aenter__(self):
        print("Entering context manager, waiting for connection")
        loop = asyncio.get_event_loop()
        connection, address = await loop.sock_accept(self._server_socket)
        self._connection = connection
        print('Accepted a connection')
        return self._connection

    async def __aexit__(self, exc_type: Optional[BaseException], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]):
        print('Exiting context manager')
        self._connection.close()
        print('Closed Connection')


async def main():
    loop = asyncio.get_event_loop()
    server_socket = socket.socket()
    server_socket.setsocket(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('127.0.0.1', 8000)
    server_socket.setblockng(False)
    server_socket.bind(server_address)
    server_socket.listen()

    async with ConnectedSocket(server_socket) as connection:
        data = await loop.sock_recv(connection, 1024)
        print(data)

asyncio.run(main)
```

### Making web requests with aiohttp

Aiohttp and web requests in general employ the concept of session. Inside the session, you can save the cookie, and keep many connections open. Because connection is resource intensive, creating a reusable pool of connections is the common practice.

```Python
import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed


@async_timed()
async def fetch_status(session: ClientSession, url: str) -> int:
    async with session.get(url) as result:
        return result.status

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = 'https://www.example.com'
        status = await fetch_status(session, url)
        print(f"status for {url} was {status}.")

asyncio.run(main())

```

ClientSession will create a default maximum of 100 connections by default.

The below code uses the aiohttp's builtin timeout function.

First, on client level, it sets the total timeout to be 1s and connection to be 0.1s, then in the `fetch_status`, it overwrites the timeout to be 0.01.

```Python
import asyncio
import aiohttp
from aiohttp import ClientSession

async def fetch_status(session: ClientSession, url: str) -> int:
    ten_millis = aiohttp.ClientTimeout(total=.01)
    async with session.get(url, timeout=ten_millis) as result:
        return result.status

async def main():
    session_timeout = aiohttp.ClientTimeout(total=1, connect=.1)
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        await fetch_session(session, "https://www.example.com")

asyncio.run(main())
```

### Running tasks concurrently, revisited

Below is a way of creating task and executing them concurrently using list comprehension

If one task throws an exception, it is actually going to halt the main process (You did not specify the try and except error for the task unit), which is not favourable.

```Python
import asyncio
from util import async_timed, delay

@async_timed()
async def main() -> None:
    delay_times = [3, 3, 3]
    tasks = [asyncio.create_task(delay(seconds)) for seconds in delay_times]
    [await task for task in tasks]

```

### Running requests concurretnly with gather

`asyncio.gather` will automatically takes in a sequence of awaitables, and if it is a coroutine, it will automatically wrap it in a task.

1. Each coroutine is automatically wrapped into a Task
2. All tasks are scheduled immediately
3. gather waits for all of them to finish

```Python
import asyncio
import aiohttp
from aiohttp import ClientSession
from chapter_04 import fetch_status
from util import async_timed

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        urls = ['https://example.com' for _ in range(1000)]
        requests = [fetch_status(session, url) for url in urls]
        status_codes = await asyncio.gather(*requests)
        print(status_codes)

asyncio.run(main())

```

Also, the `asyncio.gather` guarantees that the awaitable we pass in will complete in a deterministic order. For example, the result of the code below would acutally be [3, 1].

```Python
import asyncio
from util import delay

async def main():
    results = await asyncio.gather(delay(3), delay(1))
    print(results)

asyncio.run(main())

```

### gather with exception handling

By default, the exception wrapped in gather will be thrown after everything ended. A way to explicitly handles it is to ask the asyncio to return the Exception also.

```Python
from util import async_timed
import asyncio
import aiohttp
from chapter_04 import fetch_status


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        urls = ['https://example.com', 'python://example.com']
        tasks = [fetch_status(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exceptions = [res for res in results if isinstance(res, Exception)]
        successful_results = [res for res in results if not isinstance(res,Exception)]
        print(f'All results: {results}')
        print(f'Finished successfully: {successful_results}')
        print(f'Threw exceptions: {exceptions}')


asyncio.run(main())

```

Gather has the following two weak points:

1. Not easy to cancel the tasks. Why? because you wrap it and hand it over to gather. Now you cannot easily cancel it.
2. Gather will wait for all awaitable(tasks) to finish before output something.

### Processing requests as they complete

To counter the second problem, we can use as_completed api. This allows some task to finish and output first.

```Python

import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed

async def fetch_status(session: ClientSession, url: str, delay: int = 0) -> int:
    await asyncio.sleep(delay)
    async with session.get(url) as result:
        return result.status

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [fetch_status(session, 'https://www.example.com', 1),
                    fetch_status(session, 'https://www.example.com', 1),
                    fetch_status(session, 'https://www.example.com', 10)]

        for finished_task in asyncio.as_completed(fetchers):
            print(await finished_task)


asyncio.run(main())

```

To counter the first problem, we can use timeout, if the overall as_completed has taken longer than the timeout, each awaitable in the iterator will throw TimeoutException.

```Python

import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed

async def fetch_status(session: ClientSession, url: str, delay: int = 0) -> int:
    await asyncio.sleep(delay)
    async with session.get(url) as result:
        return result.status

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [fetch_status(session, 'https://www.example.com', 1),
                    fetch_status(session, 'https://www.example.com', 1),
                    fetch_status(session, 'https://www.example.com', 10)]

        for finished_task in asyncio.as_completed(fetchers):
            print(await finished_task)


asyncio.run(main())

```

However, behind the secene, as_completed with timeout does the following: the task that got TimeoutException is still running in the background. Also, there is no way telling which tasks got finished, you can just saw the result.

We still need better control.

### Finer-grained control with wait

By default, `asyncio.wait` works like `asyncio.gather`. The following code will have no pending tasks.

```Python

import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed
from chapter_04 import fetch_status

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = \
        [asyncio.create_task(fetch_status(session, 'https://example.com')),
         asyncio.create_task(fetch_status(session, 'https://example.com'))]
        done, pending = await asyncio.wait(fetchers)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            result = await done_task
            print(result)

asyncio.run(main())
```

And also like gather, it will not throw exception until everything is run. To handle the exception, you should handle like the following:

```Python
import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed
from chapter_04 import fetch_status
import logging

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = \
        [asyncio.create_task(fetch_status(session, 'https://example.com')),
         asyncio.create_task(fetch_status(session, 'python://example.com'))]
        done, pending = await asyncio.wait(fetchers)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            if done_task.exception() is None:
                print(done_task.result())
            else:
                logging.error("Request got an exception",
                             exc_info=done_task.exception())


asyncio.run(main())


```

This, is however problematic in the same way as `asyncio.gather`, because if you have on exception, you might want to stop all the tasks but you cannot.

In this scenario, you can use the `FIRST_EXCEPTION` option. This will make the `asycio.wait` to immediately return if an exception is raised.

The done set will consist of all the completed tasks, while the pending set will consist of still running tasks.

```Python

import asyncio
import aiohttp
from aiohttp import ClientSession
from util import async_timed
from chapter_04 import fetch_status
import logging

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = \
        [asyncio.create_task(fetch_status(session, 'python://example.com')),
         asyncio.create_task(fetch_status(session, 'https://example.com', 3)),
         asyncio.create_task(fetch_status(session, 'https://example.com', 3))]

        done, pending = await asyncio.wait(fetchers, return_when=asyncio.FIRST_EXCEPTION)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            if done_task.exception() is None:
                print(done_task.result())
            else:
                logging.error("Request got an exception",
                             exc_info=done_task.exception())

        for pending_task in pending:
            pending_task.cancel()


asyncio.run(main())

```

But this is still problematic, what if we do not want to wait for all coroutines to complete? We can use `return_when=asyncio.FIRST_COMPLETED`, and some simple loop logic.

```Python
import asyncio
import aiohttp
from chapter_04 import fetch_status
from util import async_timed

@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = 'https://www.example.com'
        pending = [asyncio.create_task(fetch_status(session, url)),
                   asyncio.create_task(fetch_status(session, url)),
                   asyncio.create_task(fetch_status(session, url))]
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            print(f'Done task count: {len(done)}')
            print(f'Pending task count: {len(pending)}')
            for done_task in done:
                print(await done_task)
asyncio.run(main())
```

**Important thing here, you can use timeout in `asyncio.wait`, and it is going to return after that timeout, thats it, you still need to manually cancel those tasks.**

**Also the best pracitice here is to always use wrapped task for `asyncio.wait`**
