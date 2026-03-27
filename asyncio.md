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

## Non-blocking database drivers

### Execute query with asyncpg

Use docker to deploy a postgre server, we can use `execute` and `fetch` to execute the sql caluse, or get asyncpg Record objects back.

In the code below, we create sql database by executing the codes, and since the `execute` itself is a coroutine, we will have to await it.
Notice that this code snippet is synchronous.

```Python

import asyncio

import asyncpg

CREATE_BRAND_TABLE = """
CREATE TABLE IF NOT EXISTS brand(
brand_id SERIAL PRIMARY KEY,
brand_name TEXT NOT NULL
);"""
CREATE_PRODUCT_TABLE = """
CREATE TABLE IF NOT EXISTS product(
product_id SERIAL PRIMARY KEY,
product_name TEXT NOT NULL,
brand_id INT NOT NULL,
FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
);"""
CREATE_PRODUCT_COLOR_TABLE = """
CREATE TABLE IF NOT EXISTS product_color(
product_color_id SERIAL PRIMARY KEY,
product_color_name TEXT NOT NULL
);"""
CREATE_PRODUCT_SIZE_TABLE = """
CREATE TABLE IF NOT EXISTS product_size(
product_size_id SERIAL PRIMARY KEY,
product_size_name TEXT NOT NULL
);"""
CREATE_SKU_TABLE = """
CREATE TABLE IF NOT EXISTS sku(
sku_id SERIAL PRIMARY KEY,
product_id INT NOT NULL,
product_size_id INT NOT NULL,
product_color_id INT NOT NULL,
FOREIGN KEY (product_id)
REFERENCES product(product_id),
FOREIGN KEY (product_size_id)
REFERENCES product_size(product_size_id),
FOREIGN KEY (product_color_id)
REFERENCES product_color(product_color_id)
);"""
COLOR_INSERT = """
INSERT INTO product_color VALUES(1, 'Blue');
INSERT INTO product_color VALUES(2, 'Black');
"""
SIZE_INSERT = """
INSERT INTO product_size VALUES(1, 'Small');
INSERT INTO product_size VALUES(2, 'Medium');
INSERT INTO product_size VALUES(3, 'Large');
"""


async def main():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )
    statements = [
        CREATE_BRAND_TABLE,
        CREATE_PRODUCT_TABLE,
        CREATE_PRODUCT_COLOR_TABLE,
        CREATE_PRODUCT_SIZE_TABLE,
        CREATE_SKU_TABLE,
        SIZE_INSERT,
        COLOR_INSERT,
    ]

    print("Creating the product database...")
    for statement in statements:
        status = await connection.execute(statement)
        print(status)
    print("Finished creating the product database!")
    await connection.close()


asyncio.run(main())
```

Similarly, we can await `fetch`, which by itself is also a coroutine.

```Python

import asyncio
from typing import List

import asyncpg
from asyncpg import Record


async def main():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )
    await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'Levis')")
    await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'Seven')")

    brand_query = "SELECT brand_id, brand_name FROM brand"
    results: List[Record] = await connection.fetch(brand_query)

    for brand in results:
        print(f"id: {brand['brand_id']}, name: {brand['brand_name']}")

    await connection.close()


asyncio.run(main())
```

### Executing queries concurrently with connection pools

You might think that using asyncio.gather would be enough, like the following code. We basically want to execute two queries concurrently

```Python

import asyncio

import asyncpg

product_query = """
SELECT
p.product_id,
p.product_name,
p.brand_id,
s.sku_id,
pc.product_color_name,
ps.product_size_name
FROM product as p
JOIN product_color as pc on pc.product_color_id = s.product_color_id
JOIN product_size as ps on ps.product_size_id = s.product_size_id
WHERE p.product_id = 100"""


async def main():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )
    print("Creating the product database")
    queries = [connection.execute(product_query), connection.execute(product_query)]
    results = await asyncio.gather(*queries)
    print(results)


asyncio.run(main())

```

However, the above code will not work. It will return asyncpg error that another task is runnning etc. The reason is that, in SQL world, one connection means one socket connection to our database. If you want concurrent results reading, you need to create multiple connections to the database and executing one query per connection. Since establishing connections is resource expensive, caching them so we can access them when needed make sense. This is commonly know as **connection pool**.

To put simply, the connection pool's size determines how many tasks(sqls) can be run concurrently at one time.

```Python

import asyncio

import asyncpg

from util import async_timed

product_query = """
select
p.product_id,
p.product_name,
p.brand_id,
s.sku_id,
pc.product_color_name,
ps.product_size_name
from product as p
join sku as s on s.product_id = p.product_id
join product_color as pc on pc.product_color_id = s.product_color_id
join product_size as ps on ps.product_size_id = s.product_size_id
where p.product_id = 100"""


async def query_proudct(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(product_query)


@async_timed()
async def query_proudct_synchronously(pool, queries):
    return [await query_proudct(pool) for _ in range(queries)]


@async_timed()
async def query_proudct_concurrently(pool, queries):
    queries = [query_proudct(pool) for _ in range(queries)]
    return await asyncio.gather(*queries)


async def main():
    async with asyncpg.create_pool(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="password",
        database="products",
        min_size=6,
        max_size=6,
    ) as pool:
        await query_proudct_synchronously(pool, 10000)
        await query_proudct_concurrently(pool, 10000)


asyncio.run(main())

```

In the above code, we create a pool of 6 connections. It is worth noticing that, create_pool is asynchornous context manager, we need to use async with.

This task is actually a mix between cpu-bound and IO-bound, there is still room for more optimization.

### Managing transactions with asyncpg

The transaction can be managed using async context manager. It will automatically roll back if exception is raised, otherwise it will automatically committed.

```Python

import asyncio

import asyncpg


async def main():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )

    async with connection.transaction():
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_1')")
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_2')")

    query = """SELECT brand_name from brand
                WHERE brand_name LIKE 'brand%'"""
    brands = await connection.fetch(query)
    print(brands)

    await connection.close()


asyncio.run(main())

```

This might be postgres-specific feature, but asyncpg allows for saving point, which means if you nested a transaction, that inner transaction got roll back, but any queries successfully excuted before it will not roll back.(Of course you need to handle the exception)

```Python
import asyncio
import asyncpg
import logging


async def main():
    connection = await asyncpg.connect(host='127.0.0.1',
                                       port=5432,
                                       user='postgres',
                                       database='products',
                                       password='password')
    async with connection.transaction():
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'my_new_brand')")

        try:
            async with connection.transaction():
                await connection.execute("INSERT INTO product_color VALUES(1, 'black')")
        except Exception as ex:
            logging.warning('Ignoring error inserting product color', exc_info=ex)

    await connection.close()


asyncio.run(main())

```

Another method might be to manage the transaction manually. we need to manually write `try, except, else` with `transaction.rollback()`, `transaction.commit()`
Notice that there is no `transaction.close()`

```Python

import asyncio

import asyncpg
from asyncpg.transaction import Transaction


async def main():
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        database="products",
        password="password",
    )
    transaction: Transaction = connection.transaction()
    await transaction.start()
    try:
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_1')")
        await connection.execute("INSERT INTO brandVALUES(DEFAULT), 'brand_2'")

    except asyncpg.PostgresError:
        print("Rolling back...")
        await transaction.rollback()
    else:
        await transaction.commit()

    query = """SELECT brand_name FROM brand
                WHERE brand_name LIKE 'brand%'"""

    brands = await connection.fetch(query)
    print(brands)

    await connection.close()


asyncio.run(main())

```

### Asynchronous generators and streaming result sets

Sometimes when you execute query, you do not want to use `fetch` to just get lots of results. You might want to stream the results. This can be done using asynchrnous generators and `async for` syntax.

An asynchrnous generator differs from a regular generator in that, instead of generating plain Python objects are elements, it generates coroutines that we can then await until we get a result.

```Python
import asyncio

from util import async_timed, delay


async def positive_integers_async(until: int):
    for integer in range(1, until):
        await delay(integer)
        yield integer


@async_timed()
async def main():
    async_generator = positive_integers_async(3)
    print(type(async_generator))
    async for number in async_generator:
        print(f"Got number {number}")


asyncio.run(main())

```

Using `cursor` will return an asynchrnous generator that we can use to stream results. By default, cursor prefetch 50 records at a time.

```Python
import asyncio
import asyncpg


async def main():
    connection = await asyncpg.connect(host='127.0.0.1',
                                       port=5432,
                                       user='postgres',
                                       database='products',
                                       password='password')

    query = 'SELECT product_id, product_name FROM product'
    async with connection.transaction():
        async for product in connection.cursor(query):
            print(product)

    await connection.close()


asyncio.run(main())

```

Notice that in the following code, we await the cursor, becuase it is both an asynchrnous generator and a coroutine in asyncpg.
We skip first 500 records, and fetch the next 100 products and print them each out to the console.

```Python
import asyncpg
import asyncio


async def main():
    connection = await asyncpg.connect(host='127.0.0.1',
                                       port=5432,
                                       user='postgres',
                                       database='products',
                                       password='password')
    async with connection.transaction():
        query = 'SELECT product_id, product_name from product'
        cursor = await connection.cursor(query) #A
        await cursor.forward(500) #B
        products = await cursor.fetch(100) #C
        for product in products:
            print(product)

    await connection.close()


asyncio.run(main())

```

The two methods above are pretty good, but what if we only want a certain number of records back?

```Python
import asyncpg
import asyncio


async def take(generator, to_take: int):
    item_count = 0
    async for item in generator:
        if item_count > to_take - 1:
            return
        item_count = item_count + 1
        yield item


async def main():
    connection = await asyncpg.connect(host='127.0.0.1',
                                       port=5432,
                                       user='postgres',
                                       database='products',
                                       password='password')
    async with connection.transaction():
        query = 'SELECT product_id, product_name from product'
        product_generator = connection.cursor(query)

        async for product in take(product_generator, 5):
            print(product)

        print('Got the first five products!')

    await connection.close()


asyncio.run(main())

```

## 6. Handling CPU-bound work

As it is mentioned in Chatper 1, due to GIL in python, multithread can only benefit IO-bound code. Therefore we can use mulitprocessing library to handle cpu-bound work.
The idea is, instead of our parent process spawning threads to parallelize things, we instead spawn subprocess to handle the work.
Each subprocess is going to have its own GIL.

```Python

import time
from multiprocessing import Process


def count(count_to: int) -> int:
    start = time.time()
    counter = 0
    while counter < count_to:
        counter += 1
    end = time.time()

    print(f"Finished counting to {count_to} in {end - start}")
    return counter


if __name__ == "__main__":
    start_time = time.time()

    to_ond_hundred_million = Process(target=count, args=(100000000,))
    to_two_hundred_million = Process(target=count, args=(200000000,))

    to_ond_hundred_million.start()
    to_two_hundred_million.start()

    to_ond_hundred_million.join()
    to_two_hundred_million.join()

    end_time = time.time()
    print(f"Completed in {end_time - start_time}")


```

Here the `start()` method can start the process immediately, and the `join()` method will block the main process until both subprocesses are done. Otherwise our program will exit almost immediately.

Also the part `if __name__ == "__main__"` is actually necessary, otherwise there is a risk of others importing your code will run process unintentionally.

### Process pools

**Process pools** is a concept similar to **Connection pools**, in that instead of a pool of connections established to database, it is a pool of created python process.

```Python

from multiprocessing import Pool


def say_hello(name: str) -> str:
    return f"Hi there, {name}"


if __name__ == "__main__":
    with Pool() as process_pool:
        hi_jeff = process_pool.apply(say_hello, args=("Jeff",))
        hi_john = process_pool.apply(say_hello, args=("John",))
        print(hi_jeff)
        print(hi_john)
```

Here the apply automatically start and join the process, and we also can get back the return value. But, the appply will block until function completes, so the code is synchronous.

A way to resolve it is to use `apply_sync`

```Python

from multiprocessing import Pool


def say_hello(name: str) -> str:
    return f"Hi there, {name}"


if __name__ == "__main__":
    with Pool() as process_pool:
        hi_jeff = process_pool.apply_async(say_hello, args=("Jeff",))
        hi_john = process_pool.apply_async(say_hello, args=("John",))
        print(hi_jeff.get())
        print(hi_john.get())


```

When we use `apply_sync`, our call starts instantly in seperate processes. When we call `get` method, our parent process will block until each process returns a value. But what if the second task finish early? Even if it finished early, we cannot get its return value immediately before the first value, that is the disadvantage here.

### Using process pool executors with asyncio

`concurrent.futures` module provides abstraction for us. This class defines two methods for running work asynchrnously.

The first is `submit`, which will take a callable and return a Future. The second is `map`, it will take a callable and a list of arguments and implement them asynchrnously, and it will return iterators.

```Python
import time
from concurrent.futures import ProcessPoolExecutor


def count(count_to: int) -> int:
    start = time.time()
    counter = 0
    while counter < count_to:
        counter += 1
    end = time.time()
    print(f"Finished counting to {count_to} in {end - start}")
    return counter


if __name__ == "__main__":
    with ProcessPoolExecutor() as process_pool:
        numbers = [1, 3, 5, 22, 1000_000_000]
        for result in process_pool.map(count, numbers):
            print(result)
```

However, this method will return the value in a deterministic way, which is not as responsive as `asyncio.as_completed`

What we can do is use this together with the asyncio's eventloop. `gather.run_in_executor` only takes a callable and does not allow us to supply function arguments, so we will need to use partial function application to build countdown calls with 0 arguments.

```Python

import asyncio
from asyncio.events import AbstractEventLoop
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import List


def count(count_to: int) -> int:
    counter = 0
    while counter < count_to:
        counter += 1
    return counter


async def main():
    with ProcessPoolExecutor() as process_pool:
        loop: AbstractEventLoop = asyncio.get_running_loop()
        nums = [1, 3, 5, 22, 100_000_000]
        calls: List[partial[int]] = [partial(count, num) for num in nums]
        call_coros = []

        for call in calls:
            call_coros.append(loop.run_in_executor(process_pool, call))

        results = await asyncio.gather(*call_coros)

        for result in results:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())

```

Here the `loop.run_in_executor` starts the running, and the `gather` method waits util every tasks is done.

If we want, we can also use `as_completed` to solve the problem we talked about earlier.

### Solving a problem with MapReduce using asyncio

```Python
import functools
from typing import Dict


def map_frequency(text: str) -> Dict[str, int]:
    words = text.split(" ")
    frequencies = {}
    for word in words:
        if word in frequencies:
            frequencies[word] += 1
        else:
            frequencies[word] = 1

    return frequencies


def merge_dictionaries(first: Dict[str, int], second: Dict[str, int]) -> Dict[str, int]:
    merged = first
    for key in second:
        if key in merged:
            merged[key] = merged[key] + second[key]
        else:
            merged[key] = second[key]
    return merged


lines = [
    "I know what I know",
    "I know that I know",
    "I don't know much",
    "They don't know much",
]

mapped_results = [map_frequency(line) for line in lines]

for result in mapped_results:
    print(result)


print(functools.reduce(merge_dictionaries, mapped_results))
```

This will be a single threaded map-reduce function....

```Python
import asyncio
import concurrent.futures
import functools
import time
from typing import Dict, List


def partition(data: List, chunk_size: int) -> List:
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


def map_frequencies(chunk: List[str]) -> Dict[str, int]:
    counter = {}
    for line in chunk:
        word, _, count, _ = line.split("\t")
        if counter.get(word):
            counter[word] = counter[word] + int(count)
        else:
            counter[word] = int(count)
    return counter


def merge_dictionaries(first: Dict[str, int], second: Dict[str, int]) -> Dict[str, int]:
    merged = first
    for key in second:
        if key in merged:
            merged[key] = merged[key] + second[key]
        else:
            merged[key] = second[key]
    return merged


async def reduce(loop, pool, counters, chunk_size) -> Dict[str, int]:
    chunks: List[List[Dict]] = list(partition(counters, chunk_size))
    reducers = []
    while len(chunks[0]) > 1:
        for chunk in chunks:
            reducer = functools.partial(functools.reduce, merge_dictionaries, chunk)
            reducers.append(loop.run_in_executor(pool, reducer))
        reducer_chunks = await asyncio.gather(*reducers)
        chunks = list(partition(reducer_chunks, chunk_size))
        reducers.clear()
    return chunks[0][0]


async def main(partition_size: int):
    with open("", encoding="urf-8") as f:
        contents = f.readlines()
        loop = asyncio.get_running_loop()
        tasks = []
        start = time.time()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            for chunk in partition(contents, partition_size):
                tasks.append(
                    loop.run_in_executor(
                        pool, functools.partial(map_frequencies, chunk)
                    )
                )
            intermediate_results = await asyncio.gather(*tasks)
            final_result = await reduce(loop, pool, intermediate_results, 500)

            print(f"Aardvark has appeared {final_result['Aardvark']} times.")
            end = time.time()
            print(f"MapReduce took: {(end - start):.4f} seconds")


if __name__ == "__main__":
    asyncio.run(main(partition_size=60000))

```

Now this will be a good example of using multiprocess MapReduce. We calculate the dictionary parallely, we calculate the final sum also parallely. Something worth revisiting in the future for sure.

### Shared data and locks

Each process has its own memory. However, in certain cases, shared state might be needed, for example, shared counter.

multiprocessing supports two kinds of shared data: values and array.

```Python

from multiprocessing import Array, Process, Value


def increment_value(shared_int: Value):
    shared_int.value = shared_int.value + 1


def increment_array(shared_array: Array):
    for index, integer in enumerate(shared_array):
        shared_array[index] = integer + 1


if __name__ == "__main__":
    integer = Value("i", 0)
    integer_array = Array("i", [0, 0])

    procs = [
        Process(target=increment_value, args=(integer,)),
        Process(target=increment_array, args=(integer_array,)),
    ]

    [p.start() for p in procs]
    [p.join() for p in procs]

    print(integer.value)
    print(integer_array[:])

```

This code works fine becasue each process is visiting different data object.

However, if we are visitng the same data piece, we migh encounter **race-condition**. A race condition occurs when the outcome of a set of operations is dependent on which operation ends first.

```Python

from multiprocessing import Process, Value


def increment_value(shared_int: Value):
    shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    for _ in range(100):
        integer = Value("i", 0)
        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]
        [p.start() for p in procs]
        [p.join() for p in procs]
        print(integer.value)
        assert integer.value == 2

```

Here, if both process reads when the integer value is still equal to 0, they will both assign the integer's value to 1.

To avoid the race conditioning, we can **synchronous** access to any shared data we want to modify. This means that when there is a tie between two operations happen, we can pick one operation to happen first. One mechansim is called **lock**. The structure allows for a single process to **lock** a section of code, and the locked section is called critical section.

Let's add the lock for our core part. Here we can just use context manager, which automatically acquire and release the lock.

However, the following code now becomes completely synchronous.

```Python

from multiprocessing import Process, Value


def increment_value(shared_int: Value):
    with shared_int.get_lock():
        shared_int.value = shared_int.value + 1


if __name__ == "__main__":
    for _ in range(100):
        integer = Value("i", 0)
        procs = [
            Process(target=increment_value, args=(integer,)),
            Process(target=increment_value, args=(integer,)),
        ]
        [p.start() for p in procs]
        [p.join() for p in procs]
        print(integer.value)
        assert integer.value == 2


```

So, it is important to use only certain code parts as the critical section.

Now a question is, how do we use process pool for the shared data? To do this, we need to define a global variable, so that every process can visit it.

```Python

import asyncio
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Value

shared_counter: Value


def init(counter: Value):
    global shared_counter
    shared_counter = counter


def increment():
    with shared_counter.get_lock():
        shared_counter.value += 1


async def main():
    counter = Value("d", 0)
    with ProcessPoolExecutor(initializer=init, initargs=(counter,)) as pool:
        await asyncio.get_running_loop().run_in_executor(pool, increment)
        print(counter.value)


if __name__ == "__main__":
    asyncio.run(main())

```

We create the counter and initilize it to 0, then pass it to process pool in the main coroutine.

### Multiple processes, multiple event loops

Although some tasks seem to be IO-dominant, it can also be beneifitial to use multiprocesses. Why? For example, we need to take the result given by Postgre, and this step still takes CPU.

What we can do is, for each process, we have its own Python Interpreter and event loop.

The following code will start 5 processes, each process run 10000 queries concurrently.

```Python

import asyncio
from concurrent.futures.process import ProcessPoolExecutor
from typing import Dict, List

import asyncpg

from util import async_timed

product_query = """
SELECT
p.product_id,
p.product_name,
p.brand_id,
s.sku_id,
pc.product_color_name,
ps.product_size_name
FROM product as p
JOIN sku as s on s.product_id = p.product_id
JOIN product_color as pc on pc.product_color_id = s.product_color_id
JOIN product_size as ps on ps.product_size_id = s.product_size_id
WHERE p.product_id = 100"""


async def query_product(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(product_query)


@async_timed()
async def query_products_concurrently(pool, queries):
    queries = [query_product(pool) for _ in range(queries)]
    return await asyncio.gather(*queries)


def run_in_new_loop(num_queries: int) -> List[Dict]:
    async def run_queries():
        async with asyncpg.create_pool(
            host="127.0.0.1",
            post=5432,
            user="postgres",
            password="password",
            database="products",
            min_size=6,
            max_size=6,
        ) as pool:
            return await query_products_concurrently(pool, num_queries)

    results = [dict(result) for result in asyncio.run(run_queries())]
    return results


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    pool = ProcessPoolExecutor()
    tasks = [loop.run_in_executor(pool, run_in_new_loop, 10000) for _ in range(5)]
    all_results = await asyncio.gather(*tasks)
    total_queries = sum([len(result) for result in all_results])
    print(f"Retrieved {total_queries} products the product database.")


if __name__ == "__main__":
    asyncio.run(main())


```

## Handling blocking work with threads

We do not always have the privilege of accessing aysnc-ready library like asyncpg. During such situation, we have no choice but to use mulithreading

### Introducing the threading module

Python interpreter runs single-threaded within a porcess due to GIL. This means that only one piece of Python bytecode can be running at one time even if we have code running in multiple threads.
This seems like Python limits us from using multithreading to any advantage, but there are few cases in which the global interpreter lock is released.
A primary one for this situation is during I/O operations. Under the hood, Python is making low-level operating system calls to perform I/O.

Let's think about the echo server case. A socket's `recv` and `sendall` are I/O-bound methods, therefore we should be able to run them in seperate threads concurrently.

In the following code, we entered an infinite loop listening for connections. Once we have a client connected, we create a new thread to run the echo function. Then we start the thread and loop again.

Since each `recv` and `sendall` operates in seperate thread per client, these opreations never block each other. They only block the thread they are running in.

```Python

import socket
from threading import Thread


def echo(client: socket):
    while True:
        data = client.recv(2048)
        print(f"Received {data}, sending!")
        client.sendall(data)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8000))
    server.listen()
    while True:
        connection, _ = server.accept()
        thread = Thread(target=echo, args=(connection,))
        thread.start()


```

A problem for this setup is that, user-created threads in Python do not recieve KeyboardInterrupt exceptions, only the main thread will recieve them. Therefore the process will stay alive because we cannot cancle those connection threads.

How to deal with this? One way is to turn our connection threads to daemon threads. When a process only has daemon threads running, the process will shutdown automatically. But this will shutdown abruptly without cleanup logic.

To do this, we'll create subclass for Thread with a cancel method.

```Python


import socket
from threading import Thread


class ClientEchoThread(Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        try:
            while True:
                data = self.client.recv(2048)
                if not data:
                    raise BrokenPipeError("Connection closed!")
                print(f"Received {data}, sending!")
                self.client.sendall(data)
        except OSError as e:
            print(f"Thread interrupted by {e} exception, shutting down!")

    def close(self):
        if self.is_alive():
            self.client.sendall(bytes("Shutting down!", encoding="utf-8"))
            self.client.shutdown(socket.SHUT_RDWR)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8000))
    server.listen()
    connection_threads = []
    try:
        while True:
            connection, addr = server.accept()
            thread = ClientEchoThread(connection)
            connection_threads.append(thread)
            thread.start()
    except KeyboardInterrupt:
        print("Shutting down!")
        [thread.close() for thread in connection_threads]

```

Overall, canceling running threads in Python is a generally tricky problem.

### Using threads with asyncio

Creating and managing multiple threads forces us to individually create and keep track of the created threads. We have use process pools from chatper6, we can use thread pools to manage threads in the same manner. Also, we can use asyncio and synchronous library like `requests` to run web requests concurrently.

```Python

import time
from concurrent.futures import ThreadPoolExecutor

import requests


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


start = time.time()

with ThreadPoolExecutor() as pool:
    urls = ["http://www.example.com" for _ in range(1000)]
    results = pool.map(get_status_code, urls)
    for result in results:
        print(result)

end = time.time()


print(f"finished requests in {end - start:.4f} second(s)")

```

The code above is not as fast as the script implementing using aiohttp. Why? Threads are creating at the operating-system level and more expensive to create than coroutines.

Let's rewrite the script using aysncio syntax.

```Python


import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

import requests

from util import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=100) as pool:
        urls = ["http://www.example.com" for _ in range(1000)]
        tasks = [
            loop.run_in_executor(pool, functools.partial(get_status_code, url))
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        print(results)


asyncio.run(main())

```

This still looks difficult, what we can do is to set the first argument in `loop.run_in_executor` as None. This will create a default threadpool, and it will closes when we exit the application, thus no need to use context manager.

A even simple choice is `asyncio.to_thread()`, which was introduced in Python 3.9.

```Python

import asyncio

import requests

from util import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    urls = ["http://www.example.com" for _ in range(1000)]
    tasks = [asyncio.to_thread(get_status_code, url) for url in urls]
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())

```

### Locks, shared data, and deadlocks

Multithreaded code is susceptible to race conditions, just like multiprocessing. However, the **memory model** of threads changes the approach slightly.

With multiprocessing, by default the processes we create do not share memory. Therefore we need to create special shared memory objects and properly initilize them so that each process can read and write to that object.

On contrary, threads **do** have access to the same memory of their parent process. This actually maken things much easier.

```Python

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests

from util import async_timed

counter_lock = Lock()
counter: int = 0


def get_status_code(url: str) -> int:
    global counter
    response = requests.get(url)
    with counter_lock:
        counter = counter + 1
    return response.status_code


async def reporter(request_count: int):
    while counter < request_count:
        print(f"Finished {counter}/{request_count} requests")
        await asyncio.sleep(0.5)


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor as pool:
        request_count = 200
        urls = ["https://www.example.com" for _ in range(request_count)]
        reporter_task = asyncio.create_task(reporter(request_count))
        tasks = [
            loop.run_in_executor(pool, functools.partial(get_status_code, url))
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        await reporter_task
        print(results)
```

Unlike mulitprocessing in which we have to create a shared Value objects that have locks built in, we'll need to create them ourselves. it turns out that we will need to import the Lock module and use the `acquire` and `release` methods around critical sections of code.

Simple lock seems to work well, but what happens when a thread tries to acquire a lock it has already acquired?

Let's look at a simple example first:

```Python

from threading import Lock, Thread
from typing import List

list_lock = Lock()


def sum_list(int_list: List[int]) -> int:
    print("Waiting to acquire lock...")
    with list_lock:
        print("Acquired lock.")
        if len(int_list) == 0:
            print("Finished summing.")
            return 0
        else:
            head, *tail = int_list
            print("Summing rest of the list")
            return head + sum_list(tail)


thread = Thread(target=sum_list, args=([1, 2, 3, 4],))
thread.start()
thread.join()

```

If you run this code, you will get stuck. Why?

The first time we acquire the lock, everything is fine. The second time we try to acquire the lock, we already have the same lock, this causes us to attempt to acquire `list_lock` the second time. This is where we code hangs, because we cannot acquire a lock that is already held by us.

Since the recursion is coming from the same thread that originated it, it should not be a problem to acquire the lock twice as it will not give rise to race-condition. The threading class use `reentrant` locks, which is a special kind of lock that can be acquired by same thread more than once. All we need to do is replacing `Lock` with `Rlock`.

```Python

from threading import RLock
from typing import List


class IntListThreadsafe:
    def __init__(self, wrapped_list: List[int]):
        self._lock = RLock()
        self._inner_list = wrapped_list

    def indices_of(self, to_find: int) -> List[int]:
        with self._lock:
            enumerator = enumerate(self._inner_list)
            return [index for index, value in enumerator if value == to_find]

    def find_and_replace(self, to_replace: int, replace_with: int) -> None:
        with self._lock:
            indices = self.indices_of(to_replace)
            for index in indices:
                self._inner_list[index] = replace_with


threadsafe_list = IntListThreadsafe([1, 2, 1, 2, 1])
threadsafe_list.find_and_replace(1, 2)
print(threadsafe_list._inner_list)

```

The same thing happens for the code above, when we call `find_and_replace`, it acquires the lock, and calls `indices_of`, which tries to acquire the lock again. If we do not use `RLock` in this case, it wilt hang forever.

A **deadlock** happens when there is a conetention over a shared resource with no resolution, and our application hangs forever.
For example, we may have a deadlock with ourselves, when we ask for a lock that is never released in our own thread. A more common situation is, thread A asks for a lock that threads B has acquired, and thread B is asking for a lock that thread A has acquired, we reach a standstill.

```Python


import time
from threading import Lock, Thread

lock_a = Lock()
lock_b = Lock()


def a():
    with lock_a:
        print("Acquired lock a from method a!")
        time.sleep(1)
        with lock_b:
            print("Acquried both locks from method a!")


def b():
    with lock_b:
        print("Acquired lock b from method b!")
        with lock_a:
            print("Acquired both locks from method b!")


thread_1 = Thread(target=a)
thread_2 = Thread(target=b)
thread_1.start()
thread_2.start()
thread_1.join()
thread_2.join()

```

How to deal with this? In this simple case, one method is to just change the order such that both methods first acquire lock A and then acquire lock B.

### Event loops in seperate threads

Here comes the situation where, we're working in an existing synchronous application and we want to incoporate asyncio.

One such situation is building desktop user interfaces. The frameworks to build GUIs usually have their own event loop. Therefore, we have to run multiple event loops in seperate threads.

Below is a simple hello-world application with Tkinter.

```Python

import tkinter
from tkinter import ttk

window = tkinter.Tk()
window.title("Hello world app")
window.geometry("200x100")


def say_hello():
    print("Hello there!")


hello_button = ttk.Button(window, text="Say hello", command=say_hello)
hello_button.pack()

window.mainloop()

```

The last command `window.mainloop()` basically starts the event loop of tkinter, and it will blocks if one oepration is taking too long, the UI will be frozen. For example, if we make `sleep(10)` for pressing a button, the UI will be stuck.

A basic idea here is, we'll have Tkinter event loop running in main thread, and we'll run the asyncio event loop in a seperate thread. When user hits the button, we submit a coroutine to the asyncio event loop to run the stress test. `asyncio.run` will block the main event loop, which is not good. We should use `call_soon_threadsafe` and `run_coroutine_threadsafe`.

Okay this part is kind of difficult, so please check code on the book.

### Using threads for CPU-bound work

The rule of thumb is multi-threading only makes sense for blocking I/O work, as I/O will release the GIL. But if we can avoid interacting with Python objects, multithreading might also provide a lot. This effect is prominent in library that is written in pure C, like hashilib and Numpy.

This gives us opportunity to interact with them using multithreading technique.

```Python
import asyncio
import functools
import hashlib
import os
import random
import string
from concurrent.futures.thread import ThreadPoolExecutor

from util import async_timed


def random_password(length: int) -> bytes:
    ascii_lowercase = string.ascii_lowercase.encode()
    return b"".join(bytes(random.choice(ascii_lowercase)) for _ in range(length))


passwords = [random_password(10) for _ in range(10000)]


def hash(password: bytes) -> str:
    salt = os.urandom(16)
    return str(hashlib.scrypt(password, salt=salt, n=2048, p=1, r=8))


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    tasks = []

    with ThreadPoolExecutor() as pool:
        for password in passwords:
            tasks.append(loop.run_in_executor(pool, functools.partial(hash, password)))

    await asyncio.gather(*tasks)


asyncio.run(main())
```

Numpy is another example here, it is generally safe to assume that, matrix operations can be potentially multithreaded for a performance win.

```Python

import asyncio
import functools
from concurrent.futures.thread import ThreadPoolExecutor

import numpy as np

from util import async_timed


def mean_for_row(arr, row):
    return np.mean(arr[row])


data_points = 400000000
rows = 50
columns = int(data_points / rows)

matrix = np.arange(data_points).reshape(rows, columns)


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        tasks = []
        for i in range(rows):
            mean = functools.partial(mean_for_row, matrix, i)
            tasks.append(loop.run_in_executor(pool, mean))

        asyncio.gather(*tasks)


asyncio.run(main())

```

This is faster than using `np.mean(matrix, axis=1)`.

