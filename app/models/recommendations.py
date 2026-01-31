from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base

class SeasonalTip(Base):
    __tablename__ = "seasonal_tips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    # Estación: spring, summer, autumn, winter
    season = Column(String, nullable=True) 
    # Meses específicos (comma separated "9,10,11") o null si aplica a toda la estación
    months = Column(String, nullable=True) 
    hemisphere = Column(String, default="South") # South (Argentina) por defecto
    category = Column(String, default="General") # Sanidad, Manejo, etc.
    isActive = Column(Boolean, default=True)

