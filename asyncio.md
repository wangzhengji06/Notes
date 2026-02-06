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
