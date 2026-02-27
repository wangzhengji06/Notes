## Database Tables

SQLAlchemy has two modules: Core and ORM.

Core: database integration logic for all supported database dialects.

ORM: allow database operations to be automatically derived from actions performed on Python objects

`create_engine()` constructs an engine given a database URL. The `engine` is used to manage connections to a database.

### models

In ORM mode, database tables are defined as Python classes. The application must create a parent class for all these calsses, which is called declarative base class.

The collection of sublcass of Base class represents the structure or schema of the database, and are generally referred to as "models" of the application.

Mapped[t] is used to define each column, t is the Python type, `mapped_column` is used to provide other options.

Database Metadata: Model.metadata, you can use it to define a naming_convention which tells SQLAlchemy how to name indexes and constraints it creates on a database.

`Model.metadata.create_all(engine)` will create database. However, it is not going to change existed schema of the tables.

### Sessions

A session object maintains the list of new, read, modified and deleted model instances. When a session is **flushed**, the changes are written to the database while keep the transaction open. A session is **committed**, the changes will be permananently written to the database.

The good part is, when error happens, it will never result in partial or incomplete data being written, and you can rollback the session.

with `session.begin()`, the context manager automatically implements rollback if error happens in a session.

So, usually a good way to use session is as follows:

```Python
with Session() as session:
    with session.begin():
        session.add(c64)
    print(c64)
```

The first context manager class is created using Session(), and the second context manager class is created using Session().begin(). The first context manger closes the session when exit, it does not commit anything, the second context manager will commit on success, and will rolback on exception.

- However since we are using fastapi, we have to manually write these operations for sessions.

### Query Execution

```Python
from db import Session
from models import Product
session=session()
from sqlalchemy import select
q=Select(Product)
r=session.execute(q)
```

Here the r is an iterator, you can use `one()`, `first()`, `all()` to get it.

You can use `session.scalars(q).all()` to get the first column for each row, which is a Python object format.

`q = select(Product).where(Product.manufacturer == "Commodore")` for filter.

`q = select(Product).where(or_(Product.year < 1970, Product.year > 1990))` to use `or_` , `not_` and `and_` for the logic.

`q = select(Product).where(Product.name.like('%Sinclair%'))` enables the use of like for blurry filtering.

`q = select(Product).order_by(Product.year.desc(), Product.name.asc())` for sorting.

`q = select(func.count(Product.id))` for aggreagation function

```Python
q = (select(
Product.manufacturer,
func.count()
)
.group_by(Product.manufacturer)
.having(func.count() >= 5)
.order_by(Product.manufacturer))
```

Use `group_by` and `having` for group by manipulation.

` num_products = func.count().label('num_products')` for label.

If you think some columns will be searched frequently, maybe it is better to add index to it.

`session.get(Product, 23)` is a query that works on primary key. Use `session.add()` and `session.delete()` to add and delete object(a row) in session.
