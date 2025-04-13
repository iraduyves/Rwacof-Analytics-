from sqlalchemy import Column, Float, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Commodity(Base):
    __tablename__ = 'commodity'
    id = Column(String, primary_key=True)
    energy = Column(Float)
    price = Column(Float)
    day = Column(Float)
    percentage = Column(Float)
    weekly = Column(Float)
    monthly = Column(Float)
    ytd = Column(Float)
    yoy = Column(Float)
    date = Column(String)

    def __repr__(self):
        return f"<Commodity(id={self.id}, name={self.name}, price={self.price}, unit={self.unit})>"
    
    def serialize(self):
        return {
            'id': self.id,
            'energy': self.energy,
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
        self.engine = None
        self.Session = None

    def create_engine(self):
        self.engine = create_engine(self.db_url)
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
        Base.metadata.create_all(self.engine)