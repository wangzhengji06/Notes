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
