from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Commodity(Base):
    __tablename__ = 'commodity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agricultural = Column(String(255))
    price = Column(Float)
    day = Column(Float)
    percentage = Column(Float)
    weekly = Column(Float)
    monthly = Column(Float)
    ytd = Column(Float)
    yoy = Column(Float)
    date = Column(String(255))

    def __repr__(self):
        return f"<Commodity(id={self.id}, name={self.name}, price={self.price}, unit={self.unit})>"
    
    def serialize(self):
        return {
            'id': self.id,
            'agricultural': self.agricultural,
            'price': self.price,
            'day': self.day,
            'percentage': self.percentage,
            'weekly': self.weekly,
            'monthly': self.monthly,
            'ytd': self.ytd,
            'yoy': self.yoy,
            'date': self.date
        }

class DatabaseService:
    def __init__(self, db_url):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Base = Base

    def create_engine(self):
        self.engine = create_engine(bind=self.engine)
        return self.engine

    def create_session(self):
        from sqlalchemy.orm import sessionmaker
        if not self.engine:
            raise Exception("Engine not created. Call create_engine() first.")
        self.Session = sessionmaker(bind=self.engine)
        return self.Session()
    def create_all(self):
        if not self.engine:
            raise Exception("Engine not created. Call create_engine() first.")
        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        if not self.engine:
            raise Exception("Engine not created. Call create_engine() first.")
        Base.metadata.drop_all(bind=self.engine)