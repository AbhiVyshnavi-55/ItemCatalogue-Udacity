from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from Data_Setup import *

engine = create_engine('sqlite:///restaurent.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete BykesCompanyName if exisitng.
session.query(RestaurentName).delete()
# Delete BykeName if exisitng.
session.query(ItemName).delete()
# Delete User if exisitng.
session.query(User).delete()

# Create sample users data
User1 = User(name="Sri Vyshnavi",
                 email="nsvs1999@gmail.com",
                 picture='http://www.enchanting-costarica.com/wp-content/'
                 'uploads/2018/02/jcarvaja17-min.jpg')
session.add(User1)
session.commit()
print ("Successfully Add First User")
# Create sample byke companys
Restaurent1 = RestaurentName(name="Sarovar",
                     user_id=1)
session.add(Restaurent1)
session.commit()

Restaurent2 = RestaurentName(name="Greenpark",
                     user_id=1)
session.add(Restaurent2)
session.commit()

Restaurent3 = RestaurentName(name="Chillies",
                     user_id=1)
session.add(Restaurent3)
session.commit()

Restaurent4 = RestaurentName(name="Dominos",
                     user_id=1)
session.add(Restaurent4)
session.commit()

Restaurent5 = RestaurentName(name="Pizza Hut",
                     user_id=1)
session.add(Restaurent5)
session.commit()

Restaurent6 = RestaurentName(name="Central Park",
                     user_id=1)
session.add(Restaurent6)
session.commit()

# Populare a bykes with models for testing
# Using different users for bykes names year also
Item1 = ItemName(name="Kaday Panner",
                       description="Desi style",
                       price="70",
                       feedback="better",
                       date=datetime.datetime.now(),
                       restaurentnameid=1,
                       user_id=1)
session.add(Item1)
session.commit()

Item2 = ItemName(name="Noodils",
                       description="soupy",
                       price="50",
                       feedback="average",
                       date=datetime.datetime.now(),
                       restaurentnameid=2,
                       user_id=1)
session.add(Item2)
session.commit()


Item3 = ItemName(name="Mancchuriya",
                       description="non-soupy",
                       price="90",
                       feedback="good",
                       date=datetime.datetime.now(),
                       restaurentnameid=3,
                       user_id=1)
session.add(Item3)
session.commit()


Item4 = ItemName(name="Layered Burger",
                       description="multiple layers",
                       price="100",
                       feedback="awesome",
                       date=datetime.datetime.now(),
                       restaurentnameid=4,
                       user_id=1)
session.add(Item4)
session.commit()

Item5 = ItemName(name="Cheesy Pizza",
                       description="cheese",
                       price="160",
                       feedback="excelent",
                       date=datetime.datetime.now(),
                       restaurentnameid=5,
                       user_id=1)
session.add(Item5)
session.commit()

Item6 = ItemName(name="Biryani",
                       description="spicy",
                       price="330",
                       feedback="nice",
                       date=datetime.datetime.now(),
                       restaurentnameid=6,
                       user_id=1)
session.add(Item6)
session.commit()


print("Your items in database has been inserted!")
