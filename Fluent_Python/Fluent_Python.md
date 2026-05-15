## The Python Data Model

### Pythonic card deck

Being pydantic actually is making good use of Python data model. The Python intepreter invokes special methods to perform basic operations, which is usually called `dunder method`.

```Python
import collections
Card = collections.namedtuple('Card', ['rank', 'suit'])

class FrenchDeck:
    ranks = [str(n) for n in range(2, 11)] + list('JQKA')
    suits = 'spades diamonds clubs hearts'.split()

def __init__(self):
    self._cards = [Card(rank, suit) for suit in self.suits
                                    for rank in self.ranks]
def __len__(self):
    return len(self._cards)

def __getitem__(self, position):
    return self._cards[position]
```

`collections.namedtuple` can create a simple class with no custom methods, like a database record. To randomly select a card, we can just do `random.choice`.

```Python
from random import choice
choice(deck)
```

This shows the advantage of making use of Python data models. The users of class dont have to memorize arbitary method. They can also use the rich libraries in Python.

```Python
deck[:3]
```

Why is this possible? Because our `__getitem__` method delegates to `[]` operator. It also makes the decks iterable. It will make `in` and `sort` work as well.

### How Special methods are needed

Special methods are meant to be called by python intepreter, not by you. You only implement them. It is better to use special methods by calling built in methods like `len`, `iter`, `str` ......

#### String Representation

`__repr__` method is used to get string representation of the object for inspection. It should return something that can be used to create the object. `__str__` is called in `print` function, and if `__str__` is not defined, Python will call `__repr__` as a fallback.

#### Boolean Value

By default, user-defined class will always be considered as truty, unless `__bool__` and `__len__` is implemeneted.

#### Length

`__len__` is also treated as a special method, because it is very practical as many objects has such feature, and Cpython usually dirrectly get the length of the collections.

## An Array Of Sequences

Container Sequences: list, tuple, collections.deque can hold different types

Flat Sequences: str, bytes, bytearray, memoryview, array.array can hold items of one type.

Container Sequneces hold references to the objects they contain, while flat sequences store the physical value of each item.

Mutable Sequences: list, bytearray, array.array, collections.deque, memoryview

Immutable Sequences: tuple, str, and bytes

### List Comprehensions and Generator Expression

#### ListComp

List comprehension is a quick way to build a **list**. So only use this when you are trying to build seuqnce, not overuse it to replace for loop.

Also Listcomp do everything map and filter do without the need of using lambda function.

Another use is it can get the Cartesian product using list comprehension

```Python
[(color, size) for color in colors for size in sizes]
```

This will generate list of tuples aranged by color, then size. It follows the same order as the nested loop.

#### Generator Expressions

To initialize tuples, arrays, and other types of sequences, you should choose generator expression over listcomp. Why? because it saves memory by yields items one by one.

Genexps use same syntax, but are enclosed in parentheses rather than brackets.

```Python
tuple(ord(symbol) for symbol in symbols)
import array
array.array('I', (ord(symbol) for symbol in symbols))
```

1. If the generator expression is the single argument in a function call, there is no need to duplicate the enclosing parentheses.
2. The array takes two arguemnts, so parentheses are mandatory.

Suppose you are trying to build 1000 \* 1000 using expression, of course using generator will save you the memory of having to build a list with a million items.

### Tuples are not just immutable lists
