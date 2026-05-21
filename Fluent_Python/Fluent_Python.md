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

### Set Theory
Set elements must be hashable, but set type is not hashable. 

```Python
found = len(set(needles) & set(haystack))
```

Don't forget, `{}` in Python means empty dict.

On ther otherhand, `frozenset` must be created by calling the constructor.
```Python
frozenset(range(10)
```

#### Set Comprehensions
```Python
{chr(i) for i in range(32,256) if 'SIGN' in name(chr(i), ''}
```

### dict and set Under the Hood
Under the hood, Python keeps a has table as some sparse array. The hash function works such that if two objects compare equal, their hash values must be equal also.

To fetch the value `my_dict[search_key]`, Python calls `hash(search_key)`, and uses the least significant bits of number as an offset to loop up a bucket. 

it will do a matching for search key and found key, and if not equal, it will use other information as offset to keep searching.

### Practical Consequences of How dict Works

An object is hashable if the 3 requirements below are met:
1. It has `hash()` function.
2. It supports `eq()` method.
3. `if a == b`, then `hash(a) == hash(b)`

because the way dict is working, while handling large quantity of records, it makes more sense to store them in a list of tuples / named tuples instead of using a list of dictionaries in JSON style. 

The order of keys in dict can change depend on insertion order. Adding items to a dict may also change the order of existing keys due to Python interpreter may decide that hash table of dict needs to grow. Therefore, if you want to iterate over keys and change at the same time, do it in *TWO STEPS*. 

Set basically share the same properties as dict.
	

## Text versus Bytes
### Character Issues
String is just a sequence of characters.

But what is character? Unicode standard explicitly seperates the identity of characters from specific byte representaitons.

The identity of a cahrachter is a number. In Unicode standard it is show as `U+xx`. 

The actual bytes that represent a cahracter depend on the encoding it use. An encoding is an algorithm that converts code points to byte sequences and vice cerca. 

### Byte Essentials
A slice of a binary sequence always produces a binary sequence of the same type - including slices of length 1. 

```Python
cafe = 'café' # this is a str, which is Unicode text
cafe = cafe.encode('utf-8') # This becomes bytes now
cafe[0] # returns the first byte as integer, because c is encoded by byte value 99.
cafe[:1] #Will return a byte object b`c` which menas a byte object containing byte 99, Python displays it as c bacause 99 is priuntable ASCII
cafe_arr = bytearray(cafe) # like bytes, but mutable
cafe_arr[-1:] # Slicing bytearray returns another bytearray
```

Therefore, 3 different displays are used, ASCII, `\n` like special character, and hexademical escape sequence.

How to initialize the bytes? 
1. bytes.fromhex('63 61 66 c3 a9') # in Decimal it would be 99 ..... that in the end translates to café.
2. str object and encoding keyword
3. A single integer to create a binary sequence of that size initialized with null bytes.
4. An object that implements the buffer protocol.

#### Structs and Memory Views
`struct` module provides functions to parse packed bytes into a tuple of fields of different types and to perform the opposite conversion, from a tuple into packed byte. 

```Python
import struct
fmt = '<3s3sHH'
with open('filter.gif', 'rb') as fp:
	img = memoryview(fp.read()) 
	
header = img[:10]
bytes(header)
struct.unpack(fmt, header)

```
### Basic Encoders/Decoders
There are a lot....


### Understanding Encode/Decode Problems
#### Coping with UnicodeEncodeError
When converting text to bytes, if a character is not defined in the target encoding, `UnicodeEncodeError` will be raised. You can cope using `encode("xxx", errors="ignore")`.

#### Coping with UnicodeDecodeError
Not every bytes hold valid UTF8 character, when you assume such encoding while converting binary sequence to text, you will get a `UnicodeDecodeError` if unexpected bytes are found.

On the other hand, sometimes you will not get error, and program will just silently decode garbage.

#### SyntaxError when Loading Modules with Unexpected Encoding
Python3 assuems UTF-8 accross platforms. if you have a py file that uses a different encoding and you want to import you can add magic coding comment.

```Python
# coding: cp1252
```

#### How to discover the encoding of a byte sequence
You can use `Chardet` package. 


#### BOM: A Useful Gremlin
BOM is a byte-order mark at the start of the byte sequence to say this UTF-16 text is little-endian or big-endian. 

UTF-8 on the other hanmd has no suchj problem, but some Windows programs put a UTF-8 BOM at the start. When you encounter such and want to use python to read, you can use encoding method `utf-8-sig`. 


### Handling Text Files
The best practice for handling text is "Unicode sandwich". Bytes should be encoded to str as early as possible. The meat is the business logic of your program. Then you encode it to byte. 

Python3 makes this very easy by using `open` that alreay takes care of the encoding. You should always explictly says the encoidng, otherwise it might default to system encoding. 


#### Encoding Defaults: A Madhouse
THere are different encoding messing around. But to summarize, what determines everything is `local.getpreferredencoding()`, this basically set the default.

Morale of the story is to never beleive in default encoding. 

### Normalizing Unicode for Saner Comparisons
`é` and `e\u0301` should be treated the same way in applications, but Python will see two different sequences and consider them not equal.

```Python
>>> s1 = 'café'
>>> s2 = 'cafe\u0301'
>>> s1, s2
('café', 'café')
>>> len(s1), len(s2)
(4, 5)
>>> s1 == s2
False
```

NFC(Normalization Form C) composes the code points to produce the shortest equivalent string.

```Python
>>> from unicodedata import normalize
>>> s1 = 'café' # composed "e" with acute accent
>>> s2 = 'cafe\u0301' # decomposed "e" and acute accent
>>> len(s1), len(s2)
(4, 5)
>>> len(normalize('NFC', s1)), len(normalize('NFC', s2))
(4, 4)
>>> len(normalize('NFD', s1)), len(normalize('NFD', s2))
(5, 5)
>>> normalize('NFC', s1) == normalize('NFC', s2)
True
```

#### Case Folding
 `str.casefold()` can convert all text to lowercase, but this does not produce the same result as `s.lower()` sometimes. For example, it will transform Greek letter.
 
#### Utility Functions for Normalized Text Matching
NFC and NFD allows the safe compariosn between Unicode strings. You can use `normalize('NFC', str)== normalize('NFC', str2)` , or `normalize('NFC', str1).casefold()`.

#### Extreme "Normalization": Taking Out DIacritics
```Python
import unicodedata
import string

def shave_marks(txt):
	"""Remove all diacritic marks"""
	norm_txt = unicodedata.normalize('NFD', txt)
	shaHved = ''.join(c for c in norm_txt
		              if not unicodedata.combining(c))
	return unicodedata.normalize('NFC', shaved)
 ```
 this function aggressively change Latin text(Also nonlatin) to pure ASCII.
 
```Python
import string
import unicodedata


def shave_marks_latin(txt):
    """Remove all diacritic marks from Latin base characters."""
    norm_txt = unicodedata.normalize("NFD", txt)
    latin_base = False
    keepers = []

    for c in norm_txt:
        if unicodedata.combining(c) and latin_base:
            continue  # ignore diacritic on Latin base char

        keepers.append(c)

        # If it isn't a combining char, it is a new base char
        if not unicodedata.combining(c):
            latin_base = c in string.ascii_letters

    shaved = "".join(keepers)
    return unicodedata.normalize("NFC", shaved)
```

This function will not remove combining marks if the previous letter is not Latin, so it only cleans the latin part. 


### Sorting Unicode Text

