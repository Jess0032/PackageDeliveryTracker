import os
from itertools import groupby
from operator import attrgetter, itemgetter

from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Package(Base):
    __tablename__ = 'package'
    package_id = Column(String, primary_key=True)
    user_id = Column(String, primary_key=True)
    status = Column(String)

    def __init__(self, package_id, user_id, laststatus):
        self.package_id = package_id
        self.user_id = user_id
        self.status = laststatus


class DBHelper:
    def __init__(self, dbname: str):
        if dbname.startswith('postgres://'):
            dbname = dbname.replace('postgres://', 'postgresql://', 1)

        self.engine = create_engine(dbname)
        Base.metadata.create_all(self.engine, checkfirst=True)

    def add(self, package_id: str, user_id: str, status: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(package_id=package_id, user_id=user_id).first()
                if db_item:
                    return 'This package already exists in database'
                session.add(Package(package_id=package_id, user_id=user_id, laststatus=status))
                session.commit()
                return 'Success insertion'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def update(self, package_id: str, status: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_items = session.query(Package).filter_by(package_id=package_id).all()
                if not db_items:
                    return 'This package not exists in database'
                for db_item in db_items:
                    db_item.status = status
                session.commit()
                return 'Success insertion'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def delete(self, user_id: str, package_id: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(package_id=package_id, user_id=user_id).first()
                if not db_item:
                    return 'Element does not exist in database'
                session.delete(db_item)
                session.commit()
                return 'Success removal'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def delete_package(self, package_id: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_items = session.query(Package).filter_by(package_id=package_id).all()
                for db_item in db_items:
                    session.delete(db_item)
                session.commit()
                return 'Success removal'

            except Exception as e:
                return f'An error occurred.\nError: {e}'

    def get_packages_from_user(self, user_id: str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package).filter_by(user_id=user_id).all()
                return db_item

            except Exception as e:
                return f'An error occurred retrieving items.\nError {e}'

    def get_packages(self):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = session.query(Package.package_id, Package.status).distinct(Package.package_id).all()
                return db_item

            except Exception as e:
                return f'An error occurred retrieving items.\nError {e}'

    def get_users_from_packages(self, package_id:str):
        with sessionmaker(self.engine)() as session:
            try:
                db_item = [x[0] for x in session.query(Package.user_id).filter_by(package_id=package_id).all()]
                return db_item

            except Exception as e:
                return f'An error occurred retrieving items.\nError {e}'
