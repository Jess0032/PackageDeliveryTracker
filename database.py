import os

from sqlalchemy import Column, String, create_engine, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Package(Base):
    __tablename__ = 'package'
    id = Column(String, primary_key=True)
    status = Column(String)
    user_id = Column(Integer)

    def __init__(self, id, laststatus, user_id):
        self.id = id
        self.status = laststatus
        self.user_id = user_id


class DBHelper:
    def __init__(self, dbname: str):
        if dbname.startswith('postgres://'):
            dbname = dbname.replace('postgres://', 'postgresql://', 1)

        self.engine = create_engine(dbname)
        Base.metadata.create_all(self.engine, checkfirst=True)

    def add(self, id: str, status: str, user_id: int):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(id=id).first()
                print(db_item)
                if db_item:
                    return 'This package already exists in database'
                session.add(Package(id=id, laststatus=status, user_id=user_id))
                session.commit()
                return 'Success insertion'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def update(self, id: str, status: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(id=id).first()
                if not db_item:
                    return 'This package not exists in database'
                db_item.status = status
                session.commit()
                return 'Success insertion'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def delete(self, user_id: int, id: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(id=id, user_id=user_id).first()
                if not db_item:
                    return 'Element does not exist in database'
                session.delete(db_item)
                session.commit()
                return 'Success removal'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def get_items(self, user_id: int):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(user_id=user_id).all()
                return db_item

            except Exception as e:
                return f'An error occurred retrieving items.\nError {e}'

    def get_users(self):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package.user_id).distinct().all()
                return db_item

            except Exception as e:
                return f'An error occurred retrieving items.\nError {e}'
