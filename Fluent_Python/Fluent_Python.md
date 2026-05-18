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

When using Tuple, the number of itmes is often fixed and the order is always vital.

#### Tuple Unpacking

The only requirement for tuple unpacking is that the iterable yields exactly one item per variable in the receiving tuple.

```Python
lax_coordinates = (33, -118)
latitude, longitude = lax_coorinates
```

The above example is assigning items from an itertable to a tuple of variables. This works for any iterable!

```Python
a, b, *rest = range(5)
rest
[2, 3, 4]

*head, b, c, d = range(5)
head
[0, 1]

name, cc, (latitude, longitude) = (xx, yy, (xx, yy))
```

#### Named Tuples

`collection.namedtuple` is a factory that produces subclass of tuple enhanced with field names and a class name. A normal object stores its feild in `__dict__`, which is memory-costly, but named tuple does not have that.

```Python
City = namedtuple('City', 'name country population')
delhi_data = ('Delhi_NCR', 'IN', (LatLong(20,30)))
delhi = City._make(delhi_data) # dehli = City(*dehli_data)
delhi._asdict()
```

#### Tuples as Imutable Lists

Tuples support all the list mothods except modifcation ones. Also, it lacs `_reversed_` method, but `reserved(my_tuple)` will work without it.

### Slicing

#### Slice Objects

s[a:b:c] will produce a slice object `slice(a,b,c)`, and to evaluate `seq[start:stop:step]`, Python calles `seq._getitem_(slice(start, stop, step))`

#### Multidimensional Slicing and Ellipsis

You can do multidimensional slicing using something like a[i, j] which is used in `numpy`. Python will inherently call `a._getitem_((i, j))`.

`x[i, ...]` is a shortcut for `x[i, :, :, :]`.

#### Assigning to Slices

```Python
l = list(range(10))
l[2:5] = [20, 30]
k[2:5] = 100 # THis will not work
```

WHen the target of assignment is slice, right side must be an iterable object.

### Using + and \* with Sequences

Python programmers expect sequneces support + and \*. A new object will be created as a result of concatenation.

#### Buliding Lists of lists

When we want to initialize a list with a certain number of nested lists, the best way is to use a list comprehension.

```Python
board = [['_'] * 3 for i in range(3)]
board_2 = [['_'] * 3] * 3]
```

The first is like the following:

```Python
row = ['_'] * 3
board = []
for i in range(3):
	board.append(row)
```

The second is like this:

```Python
board = []
for i in range(3):
	row = ['_'] * 3
	board.append(row)
```

In short it is doing shallow copy with the `*` mark.

### Augmented Assignment with Sequences

`+=` and `*=` is implemented by `_iadd_` and `_imul_` special methods. If the two methods are not evaluated, it will fall back to `a = a + b` and `a = a * b`.

List using `+=` and `*=` will keep the same id.

#### A += Assignment Puzzler

```Python
t = (1, 2, [30, 40])
t[2] += [50, 60]
```

What would happen is, the tuple will change and error will be raised. Puting mutable items in tuples is not a good idea.

### list.sort and the sorted Built-in Function

The `list.sort` will sort in place. In contrast, `sorted` will create a new list and returns it.

### Managing Ordered Sequences with bisect

`bisect` uses binary search for needle in haystack. This requires the list to be sorted.

`bisect.bisect_left(HAYSTACK, needle)` Find the first insertion place before the first existing duplicate element. You can guess what `bisect_right` does.

`bisect.insort_left(seq, item)` will insert while keep the sequence being sorted.

### When a List is Not the Answer

List is not always the answer, for example, if you are constantly adding something to the head and tail, maybe consider `deaue`. If you are storing large data, maybe use `array`. If you have a lot of containment checks, maybe use `set`.

#### Memory Views

a shared-memory sequence type that lets you handle slices of array without copying bytes. Used when you want to modify existing binary data without copying it.

#### Deque

Thread-safe, can have maximum length. But removing items from middle of a deque is not as fast.

## Dictionaries and Sets

### Generic Maping types
The inheritance relationship: Container(__continas__) / Iterable(__Iter__) / Sized(__len__) -> Mapping (__getitem__ get items keys values) -> MutableMapping(clear pop popitem setdefault update)

Usually, specialized mapping often extends `dict` or `collections.UserDict`. ABC is only used like `isinstance(my_dict, abc.Mapping)`.

The limitation is all keys must be hashable. What things are hashable? If a==b, then hash(a) == has(b), this is required. str, bytes, numeric types. User created objects are by default hashable, but if it implements `__eq__`, it may only be hashable if all its attributes are immutable. 

### dict Comprehensions
```Python
{country: code for code, country in DIAL_CORES}
```

### Overview of Common Mapping Methods
The interesting one here is `d.update(m, [**kargs]`. It is am example of duck typing. It checks whether m has a `keys` method, and if it does it will assume a mapping. Otherwise it will fall bakcs to iterating over `m`, assuming its items are `(key, value)`. 

#### Setdefault
```Python
my_dict.setdefault(key, []).append()
```

This is the same as 
```Python
 if key not in my_dict:
	my_dict[key] = []
my_dict[key].append(new_value)
```

### Mappings with Flexible Key Lookup
When you want to get something if a missing key is searched, there are two methods. 1. Use `defaultdict`. Second, use `__missing__` method.

#### Defaultdict
if you do `dd = defaultdict(list)`, what is happening is, it will call list() to create new object, insert the list into dd using `new-key` as key, and returns a reference to that list. The callable is `default_factory`. 

#### __missing__ method
`__missing__` is not in `dict` class, but if you subcalss dict, and provide a `__missing__` method, the `dict.__getitem__` will call it whenever a key is not found. 
```Python
class StrKeyDict0(dict):
	def __missing__(self, key):
		if isinstance(key, str):
			raise KeyError(key)
		return self[str(key)]
	
	def get(self, key, default=None):
		try:
			return self[key]
		except KeyError:
			return default
			
	def __contains__(self, key):
		return key in self.keys() or str(key) in self.keys() 
```
here the `[]` resolve to `__getitem__` which allows the call to `__missing__`. Note: xx in dict.keys() is very efficient, because .keys() returns a view that kind of like a set.

### Variations of dict
`OrderedDict` allows for iteration over items in a preditable order.

`ChainMap` holds a list of mappings that can be searched as one. Useful to interpreters for languages with nested scopes.

`Counter` can be used to count instances of hashable objects. `most_common([n])` is also very useful.

`UserDict` is designed to be subclassed. You should subclass it instead of `dict`, as a metter of fact.

### Subclassing UserDict
The problem with dict is that it has a lot of shortcuts that might make your overwritten methods fail unexpectedly. 

```Python
class StrKeyDict(collections.UserDict):

	def __missing__(self, key):
		if isinstance(key, str):
			raise KeyError(key)
		return self[str(key)]
	
	def __contains__(self, key):
		return str(key) in self.data #data here holds the actual items
		
	def __setitem__(self, key, item):
		self.data[str(key)] = item
```
Because UserDict subclasses MutableMapping, you have `update` method and `get` method. 

### Immutable Mappings
We might not want the users to make change to maping. `MappingProxyType` is such read-only instance from a dict. 

`d_proxy = MappingProxyType(d)` where d is a inner mapping. We can expose the ProxyType to user while the internal dict to ourselves.

