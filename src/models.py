"""Data models for pension calculation"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


@dataclass
class UserData:
    """User data structure for pension calculation"""
    age: int
    gender: str  # "male" or "female"
    gross_salary: float  # monthly gross salary in PLN
    work_start_year: int
    work_end_year: Optional[int] = None
    industry: Optional[str] = None
    position: Optional[str] = None
    company: Optional[str] = None
    zus_account_balance: Optional[float] = None
    zus_subaccount_balance: Optional[float] = None
    sick_leave_days_per_year: Optional[float] = None
    desired_pension: Optional[float] = None  # How much pension user wants (PLN/month)


class PensionCalculationRequest(BaseModel):
    """Request model for pension calculation"""
    user_data: Dict[str, Any]
    prompt: str = Field(default="", description="Custom Polish prompt for Perplexity API")


class PensionCalculationResult(BaseModel):
    """Result structure for pension calculation"""
    current_pension_projection: float = Field(..., description="Projected pension amount in PLN")
    indexed_pension_projection: float = Field(..., description="Indexed pension amount in PLN")
    replacement_rate: float = Field(..., description="Replacement rate as percentage")
    years_to_work_longer: Optional[int] = Field(None, description="Additional years needed")
    sick_leave_impact: Optional[float] = Field(None, description="Impact of sick leaves")
    salary_variability_impact: Optional[float] = Field(None, description="Impact of salary changes")
    minimum_pension_gap: Optional[float] = Field(None, description="Gap to minimum pension")
