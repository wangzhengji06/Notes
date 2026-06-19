## CMake commands
Create a file for Gnu make/ninja etc to run
```bash
cmake -S . -B build
```

Build the final target
```bash
cmake --build build
```

## Basic CMake Usage

### Different message and leve
```bash
message("hello world!")

message(STATUS "HELLO World!")

```

### Set different variable / cache variable

```bash
set(NAME "Alice")

set(NAME "Alice" CACHE STRING "Name of Person to be greeted")
```


Both commands set vairable Name and assign it to Alice. But cache variable can be rememebered next time you configure. Also you can use terminal to do something 

```bash
cmake -S . -B build -DNAME=Steve
```

-D can overwrite basically anything in the code.

```cmake
"${VAR${VAR_NUM}}"
```

The above will work!

Unset a variable, if it is cahce you have to specify that

```cmake
unset(MYVAR CACHE)
```

If you want to read variable of environment

```cmake
$ENV{PATH}
```

Comment:

```cmake
# 
#[[
Some
Good
Thing 

happenes
]] 

```


Math Operations:
```Cmake
set(X 10);
set(Y 3);
math(EXPR x "(${X} * 4) * (33 / ${Y})")
```
This will make x the result of mathmatic operations.


## If-statement

```Cmake
if (TRUE)
  message(STATUS "Evaluation is true.")
else()
  message(STATUS "Evaluation is False.")
endif()
```

Here the crazy thing is, not only TRUE evaluates to true, ON, YES, any nonzero number also evaluates to true.

```Cmake
if ( 3.13 GREATER 3.7)

if ( 3.13 VERSIONGREATER 3.7)
```

Another useful comparioson is `STREQUAL`.


Check whether something is defined.

```Cmake
if (DEFINED myvar)
```

A thing here, if you are inside the if clause, you do not have to write `${}` for a variable. However, it changes the rule.
Before, it it is anything we know that should evaluate to true, it will be true, otherwise false. Now, if it is anything that should evaluate to false, it is false, others will be true.

Besides there is auto referencing in Cmake...

## CMakes Lists and Loops

```Cmake
set(CITIES "Los Angles" Chicago "New York")
```

```Cmake
foreach(CITY IN LISTS CITIES)
  message(STATUS "This city is " ${CITY})
endforach()
```


You can concatenate very easily

```Cmake
foreach(CITY IN LISTS CITIES ITEMS HOUSTON ORLANDO)
  message(STATUS "This city is : ${CITY}")
endforeach()
```


You can also use iloop to loop for a range, notice though that it is inclusive

```Cmake
foreach(ILOOP RANGE 3) 
  message(STATUS "ILOOP: ${ILOOP}")
endforeach()
```

You can also add endpoint, or also add the step!

```Cmake
foreach(ILOOP RANGE 2 10 2)
  message(STATUS "ILOOP: ${ILOOP}")
endforeach()
```


While loop 

```Cmake
set(ILOOP 0)
while(ILOOP LESS 3)
  message(STATUS "ILOOP ${ILOOP}")
  math(EXPR ILOOP "${ILOOP} + 1")
endwhile()

```


## Macro and Function

### Macro

```Cmake
macro(print_greeting)
  message(STATUS "Hello ${GREET_NAME}")
endmacro()

set(GREET_NAME "Alice")
print_greeting()
```


Macro is just doing a very simple plugin. It shares the scope to the place that calls it.


```Cmake
macro(print_greeting)
  message(STATUS "Hello ${GREET_NAME}")
endmacro()

set(GREET_NAME "Alice")
print_greeting()

macro(print_greeting2 INPUT_NAME)
  message(STATUS "Hello ${INPUT_NAME}")
  message(STATUS "Hello ${GREET_NAME}")
  if (DEFINED INPUT_NAME)
    message(STATUS "INNPUT_NAME is defined.")
  else()
    message(STATUS "INPUT_NAME is not defined.")
  endif()
endmacro() 

print_greeting2( ${GREET_NAME})

```

Here the result will tell you that INPUT_NAME is never defined. Why? Because macro just means plugging in. not variable. 

```Cmake
macro(pass_value MYVAR)
  message(STATUS "In pass_value")
  message(STATUS "   MYVAR: ${MYVAR}")
endmacro()


set(CITY Nashville)
pass_value( ${CITY} )
pass_value( CITY )
```

Notice here that it will takes your city literally.

How to assign something inside macro? You have to use ${}. Why? Because it is just plugging in. macro is doing `MYVAR=TESTVAR` under the hood, so you use ${} to decode it.

```Cmake
macro(set_to_three MYVAR)
  message(STATUS "MYVAR: ${MYVAR}")
  set(${MYVAR} "3")
endmacro()

set_to_three( TESTVAR )
message(STATUS "TESTVAR RIGHT NOW IS ${TESTVAR}")
```

Read the following example and you will have a good understanding of macro

```Cmake
macro(custom_add X_IN Y_IN SUM_OUT)
  math(EXPR ${SUM_OUT} "${X_IN} + ${Y_IN}")
endmacro()

set(X 3)
set(Y 5)
set(SUM "asdf")

custom_add(${X} ${Y} SUM)
message(STATUS "SUM after macro: ${SUM}")
```

### Function

Function has scope. THat is like the only difference here

```Cmake
function(print_greeting)
  message(STATUS "Hello ${GREET_NAME}")
  set(GREET_NAME "Bob")
  message(STATUS ${GREET_NAME})
endfunction()

set(GREET_NAME "Alice")
print_greeting()
message(STATUS ${GREET_NAME})
```

This will print Alice, Bob, Alice. Here you are just setting the local copy of the GREET_NAME. 


```Cmake
function(print_greeting)
  message(STATUS "Hello ${GREET_NAME}")
  set(GREET_NAME "Bob" PARENT_SCOPE)
  message(STATUS ${GREET_NAME})
endfunction()

set(GREET_NAME "Alice")
print_greeting()
message(STATUS ${GREET_NAME})
```

Here it will print Alice, Alice, Bob. Why? we indeed modify the one at the parent scope, but the function scope still has the same copy, and it knows that you are not changing its local copy.

