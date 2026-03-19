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
q=select(Product)
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

## One-To-Many Relationships

When should you use relationship? As a rule of thumb, when you find that information is being duplicated, you should consider the benefits of removing this duplication through the addition of a new table and a relationship.

To define a one to many relationship, the "many" sides should include a foreign key column that reference the "one" side.

```Python

    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturers.id"), index=True
    )

```

This leaves a problem that when you use `session.get(Product, 127)` and you want to directly call the column, you can only call `p.manufacturer_id`. This creates complication.

Luckily we can overcome this problem using orm module.

```Python
Product:
    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="products")


Manufacturer:
    products: Mapped[list["Product"]] = relationship(back_populates="manufacturer")

```

From `one`'s side, the Manufacturer becomes bunch of products, which is a list, while from `many`'s side, each product is associated with one manufacturer.

How do we import data into the database with the newly defined models?

```Python

    with Session() as session:
        with session.begin():
            with open("products.csv") as f:
                reader = csv.DictReader(f)
                all_manufacturers = {}
                for row in reader:
                    row["year"] = int(row["year"])

                    manufacturer = row.pop("manufacturer")
                    p = Product(**row)

                    if manufacturer not in all_manufacturers:
                        m = Manufacturer(name=manufacturer)
                        session.add(m)
                        all_manufacturers[manufacturer] = m
                    all_manufacturers[manufacturer].products.append(p)


```

The `append()` call on the products relationship attribute achieves two things: 1. it links the manufacturer to the product through foreign_key, which will be automatically set when hte transaction is committed. 2. it indirectly includes the new product in the database session, because it is referenced by the manufacturer instance which has been explicitly added before. This automatic addition of a child to the session when the parent is already there is called **cascade**.

```Python
p = session.scalar(select(Product).where(Product.name == 'ZX Spectrum'))
p.manufacturer.name
p.manufacturer.products
```

THis factor allows the above command to be run in a python session.

```Python

q = select(Product.name, Manufacturer.name).join(Product.manufacturer)

```

Here we want to get the product name and manufacturer name together, this needs to be done using join. Since the two relationship objects are linked through the `back_populates` options, in general it does not matter which of the two is given in the join() clause.But, whowever being joined will appear on the left side for sql query. However in this case it does not matter.

Under the hood, it does the following:

```Python

>>> print(q)
SELECT products.name, manufacturers.name AS name_1
FROM products JOIN manufacturers ON manufacturers.id = products.manufacturer_id

```

Of course it is worth appreciation how sqlalchemy figured out the join condition by itself.

### Lazy vs Eager relationship

Let's select a manufacturer and try to check its products.

```Python
m = session.scalar(select(Manufacturer).where(Manufacturer.name == 'Texas Instruments'))
>>> m.products
2026-03-05 17:36:25,097 INFO sqlalchemy.engine.Engine SELECT products.id AS products_id, products.name AS products_name, products.manufacturer_id AS products_manufacturer_id, products.year AS products_year, products.country AS products_country, products.cpu AS products_cpu
FROM products
WHERE ? = products.manufacturer_id
2026-03-05 17:36:25,098 INFO sqlalchemy.engine.Engine [generated in 0.00039s] (66,)
[Product(132, "TI-99/4"), Product(133, "TI-99/4A")]

```

What if we do that again?

```Python
>>> m.products
[Product(132, "TI-99/4"), Product(133, "TI-99/4A")]

```

The sqlalchemy is "lazy" loading the relationships. Also tHe so called products is not really a column inside the table.

What problem might this bring?

```Python
q = select(Product)
for p in session.scalars(q):
    print(p.name, p.manufacturer.name)
```

This will run a lot of queries as a result. How to avoid this pattern?

1. Override it using options

We can use `joinedload`. The `select` loader is a "lazy" loader, because the qeury for related objects is delayed until the relationship attribute is accessed for the first time.

The `joined` loader, on the other hand is an `eager` loader, because the relationship data is requested at the same time the parent object is.

```Python
 q = select(Product).options(joinedload(Product.manufacturer))
```

The above code tells sqlalchemy, please bring the manufacturer relationship into the session using joined loader.

2. Change the default behavior

```Python
manufacturer: Mapped['Manufacturer'] = relationship(lazy='joined', back_populates='products')
```

There are also a bunch of other loaders you can choose.

### Deletion of Related Objects with a Cascade

In a One-To-Many relationship, if you try to delete that **one**, and that **one** is associated with **many** that still has foreign_key pointed to that one, this will makes the deletion failed when you try to commit the session.

How to deal with it? Automatic operations such as the attempt to clear foreign keys of an item that is about to be deleted are called **cascades**. In simple words, sqlalchemy will apply change to children objects in a relationship as a result of an action preformed on the parent object.

There are two cascade configurations that are used the most.

1. 'save-update, merge': default. Child objects are automatically included in the session if parent has been added to it. If parent is deleted, the foreign key will be set to None.
2. 'all, delete-orphan': cover all the cascades, and children will also be deleted when they are removed from their relationships.

Defined in the `one` part:

```Python
    products: Mapped[list["Product"]] = relationship(
        cascade="all, delete-orphan", back_populates="manufacturer"
    )
```

Now if you delete a manufacturer, the related productes will also be deleted.

Sometimes, you want to delete the relationship between two objects, without deleting the objects themselves.
Please make sure the cascade configuration does not have `delete-orphan`, and the foreign key is nullable.

From the `one` side:

```Python
p = session.get(Product, 1)
m = p.manufacturer
m.products.remove(p)
```

From the `many` side:

```Python
p = session.get(Product, 2)
p.manufacturer = None
session.commit()
```

## Many-To-Many Relationships

In a standard one-to-many relationships, the "many" side adds a foreign key that points to the "one" side.

However, for a many-to-many relationship, we need a join table.

### A Simple Many-To-Many Relationship Implementation

We make use of a third table called **join** table. The each side establish a one-to-many relationship to that table, which means there should be foreign keys in that table.

Because join table does not need to be translated into a Python Object, it is usually suggested to use `Table` class from sqlalchemy core module instead of letting it inherit from `Model` class

```Python
ProductCountry = Table(
    "products_countries",
    Model.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True, nullable=False),
    Column("country_id", ForeignKey("countries.id"), primary_key=True, nullable=False),
)
```

This table declares two foreign keys as primary keys. When multiple keys are assigned as primary keys, SQLAlchemy creates a composite primary key.

```Python
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Model

ProductCountry = Table(
    "products_countries",
    Model.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True, nullable=False),
    Column("country_id", ForeignKey("countries.id"), primary_key=True, nullable=False),
)


class Product(Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturers.id"), index=True
    )
    year: Mapped[int] = mapped_column(index=True)
    country: Mapped[Optional[str]] = mapped_column(String(32))
    cpu: Mapped[Optional[str]] = mapped_column(String(32))

    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="products")
    countries: Mapped[list["Country"]] = relationship(
        secondary=ProductCountry, back_populates="products"
    )

    def __repr__(self):
        return f'Product({self.id}, "{self.name}")'


class Country(Model):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True, unique=True)

    products: Mapped[list["Product"]] = relationship(
        secondary=ProductCountry, back_populates="countries"
    )

    def __repr__(self):
        return f'Country({self.id}, "{self.name}")'


class Manufacturer(Model):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    products: Mapped[list["Product"]] = relationship(
        cascade="all, delete-orphan", back_populates="manufacturer"
    )

    def __repr__(self):
        return f'Manufacturer({self.id}, "{self.name}")'
```

A similar thing here is, both Products and Countries need to hold the relationships. Here the `secondary` argument tells SQLAlchemy that its relationship is supported by a secondary table.

The way of importing the data into database still is the same. We first remove the manufacturer and countries for each row and extract products. Then we first add manufacturer, then add the products belong to it. for countries, because it is many to many, we will have to do a loop first.

```Python
import csv

from db import Model, Session, engine
from models import Country, Manufacturer, Product


def main():
    Model.metadata.drop_all(engine)  # warning: this deletes all data!
    Model.metadata.create_all(engine)

    with Session() as session:
        with session.begin():
            with open("products.csv") as f:
                reader = csv.DictReader(f)
                all_manufacturers = {}
                all_countries = {}
                for row in reader:
                    row["year"] = int(row["year"])

                    manufacturer = row.pop("manufacturer")
                    countries = row.pop("country").split("/")
                    p = Product(**row)

                    if manufacturer not in all_manufacturers:
                        m = Manufacturer(name=manufacturer)
                        session.add(m)
                        all_manufacturers[manufacturer] = m
                    all_manufacturers[manufacturer].products.append(p)

                    for country in countries:
                        if country not in all_countries:
                            c = Country(name=country)
                            session.add(c)
                            all_countries[country] = c
                        all_countries[country].products.append(p)


if __name__ == "__main__":
    main()
```

Notice here that because it is a many-to-many relationship, instead of writing `all_countries[country].products.append(p)`, we can do `p.countries.append(all_countries[country])` instead.

### Running query for many-to-many relationship

We can execute the query using the following way, notice that we use join too here.

```Python
>>> country_count = func.count(Country.id).label(None)
>>> q = (select(Product, country_count).join(Product.countries).group_by(Product).having(country_count>=2).order_by(Product.name))
>>> session.execute(q).all()
[(Product(143, "Komputer 2086"), 2), (Product(142, "Timex Computer 2068"), 3), (Product(138, "Timex Sinclair 1000"), 3), (Product(139, "Timex Sinclair 1500"), 3), (Product(140, "Timex Sinclair 2048"), 3)]
```

This join here is interesting because we cannot achieve this if we are using SQL.
Under the hood, it does this:

```Python
>>> print(q)
SELECT products.id, products.name, products.manufacturer_id, products.year, products.cpu, count(countries.id) AS count_1
FROM products JOIN products_countries AS products_countries_1 ON products.id = products_countries_1.product_id JOIN countries ON countries.id = products_countries_1.country_id GROUP BY products.id, products.name, products.manufacturer_id, products.year, products.cpu
HAVING count(countries.id) >= :param_1 ORDER BY products.name
```

The one-to-many and many-to-many relationships can be used together, and this opens the door to even more interesting queries.

```Python
>>> country_count = func.count(Country.id.distinct()).label(None)
>>> q = select(Manufacturer, country_count).join(Manufacturer.products).join(Product.countries).group_by(Manufacturer).having(country_count>=2)
>>> session.execute(q).all()
[(Manufacturer(70, "Timex Sinclair"), 4)]
```

There is reason we use distinct here, because it is very easy to generate multiple rows when you are doing multiple joins.

### Deleting from Many-To-Many Relationships

Many-To-Many relationships that are configured with the `secondary` option has the advantage that SQLAlchemy does all the maintenance work on the join table.

**When an entity is deleted, SQLAlchemy finds all the entities on the otherside and remove the links.**

Deleting an entity entirely:

```Python
>>> c = session.get(Country, 22)
>>> c
Country(22, "Portugal")
>>> p = session.get(Product, 138)
>>> p.countries
[Country(1, "UK"), Country(3, "USA"), Country(22, "Portugal")]
>>> session.delete(c)
>>> p.countries
[Country(1, "UK"), Country(3, "USA")]
```

Removing link without deleting entity:

```Python
>>> c = session.get(Country, 1)
>>> p = session.get(Product, 138)
>>> c
Country(1, "UK")
>>> p
Product(138, "Timex Sinclair 1000")
>>> p.countries.remove(c)
>>> session.commit()
>>> p.countries
[Country(3, "USA")]
>>>
```

There is no such thing as `delete-orphan`, some record can have 0 links:

```Python
>>> c = session.get(Country, 1)
>>> c
Country(1, "UK")
>>> p = session.get(Product, 1)
>>> p
Product(1, "Acorn Atom")
>>> p.countries
[Country(1, "UK")]
>>> c.products.remove(p)
>>> p.countries
[]
```

### Database Migration

You need to install the python library `alembic`. Also you need to create a folder using `alembic init migrations`. Here you created a folder called migrations.

The detailed setup is a little hard to follow, maybe reference the book by that time.
