## The Basics

### Hello, World!

`cout` is pronounced as "see-out", and is an abbreviation of "character output stream". `//` is served as a comment marker.

Every C++ function must have a function called `main` to tell it where to start executing.

Compile -> Link. Compile error and Linker error are easy to find while the run-time error is hard to find. :

```cpp
improt std;
int main()
{
    std::cout<<"Hello, World!\n";
    return 0;
}
```
