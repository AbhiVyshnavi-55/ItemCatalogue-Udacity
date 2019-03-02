import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    picture = Column(String(300))


class RestaurentName(Base):
    __tablename__ = 'restaurentname'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="restaurentname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self.name,
            'id': self.id
        }


class ItemName(Base):
    __tablename__ = 'itemname'
    id = Column(Integer, primary_key=True)
    name = Column(String(350), nullable=False)
    description = Column(String(1500))
    price = Column(String(150))
    feedback = Column(String(150))
    date = Column(DateTime, nullable=False)
    restaurentnameid = Column(Integer, ForeignKey('restaurentname.id'))
    restaurentname = relationship(
        RestaurentName, backref=backref('itemname', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="itemname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self. name,
            'description': self. description,
            'price': self. price,
            'feedback': self. feedback,
            'date': self. date,
            'id': self. id
        }

engin = create_engine('sqlite:///restaurent.db')
Base.metadata.create_all(engin)
