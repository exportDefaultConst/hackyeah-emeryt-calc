"""Database models and configuration for storing pension calculation results"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pension_calculations.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class PensionCalculationRecord(Base):
    """Model for storing pension calculation results"""
    __tablename__ = "pension_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # User data (denormalized for easy querying)
    age = Column(Integer)
    gender = Column(String(10))
    gross_salary = Column(Float)
    work_start_year = Column(Integer)
    work_end_year = Column(Integer, nullable=True)
    industry = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    desired_pension = Column(Float, nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Full user data as JSON
    user_data_json = Column(JSON)
    
    # Calculation results
    monthly_pension = Column(Float, nullable=True)
    replacement_rate = Column(Float, nullable=True)
    calculation_method = Column(String(50))  # "local" or "ai"
    
    # Full result as JSON
    result_json = Column(JSON)
    
    # Metadata
    calculation_date = Column(String(50))
    sanity_check_status = Column(String(20), nullable=True)
    
    def to_dict(self):
        """Convert record to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_data": {
                "age": self.age,
                "gender": self.gender,
                "gross_salary": self.gross_salary,
                "work_start_year": self.work_start_year,
                "work_end_year": self.work_end_year,
                "industry": self.industry,
                "position": self.position,
                "company": self.company,
                "desired_pension": self.desired_pension,
                "postal_code": self.postal_code,
            },
            "user_data_full": self.user_data_json,
            "results": {
                "monthly_pension": self.monthly_pension,
                "replacement_rate": self.replacement_rate,
                "calculation_method": self.calculation_method,
                "sanity_check_status": self.sanity_check_status,
            },
            "result_full": self.result_json,
            "calculation_date": self.calculation_date
        }


def init_db():
    """Initialize database - create tables if they don't exist"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_calculation_result(user_data_dict: dict, result: dict, calculation_method: str = "local"):
    """
    Save calculation result to database
    
    Args:
        user_data_dict: User data dictionary
        result: Calculation result dictionary
        calculation_method: "local" or "ai"
    
    Returns:
        PensionCalculationRecord: Saved record
    """
    db = SessionLocal()
    try:
        record = PensionCalculationRecord(
            # User data
            age=user_data_dict.get("age"),
            gender=user_data_dict.get("gender"),
            gross_salary=user_data_dict.get("gross_salary"),
            work_start_year=user_data_dict.get("work_start_year"),
            work_end_year=user_data_dict.get("work_end_year"),
            industry=user_data_dict.get("industry"),
            position=user_data_dict.get("position"),
            company=user_data_dict.get("company"),
            desired_pension=user_data_dict.get("desired_pension"),
            postal_code=user_data_dict.get("postal_code"),
            user_data_json=user_data_dict,
            
            # Results
            monthly_pension=result.get("monthly_pension"),
            replacement_rate=result.get("replacement_rate") or result.get("meta", {}).get("replacement_rate"),
            calculation_method=calculation_method,
            result_json=result,
            
            # Metadata
            calculation_date=result.get("meta", {}).get("calculation_date") or result.get("calculation_date", datetime.now().isoformat()),
            sanity_check_status=result.get("sanity_check", {}).get("status")
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_calculation_records(page: int = 1, per_page: int = 20):
    """
    Get paginated calculation records
    
    Args:
        page: Page number (1-indexed)
        per_page: Records per page
    
    Returns:
        dict with records, pagination info
    """
    db = SessionLocal()
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        total = db.query(PensionCalculationRecord).count()
        
        # Get paginated records
        records = db.query(PensionCalculationRecord)\
            .order_by(PensionCalculationRecord.timestamp.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "records": [record.to_dict() for record in records],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    finally:
        db.close()
