from pydantic import BaseModel, HttpUrl, Field, EmailStr
from datetime import datetime
from typing import Optional, List


class SourceOut(BaseModel):
	id: int
	name: str
	url: str
	slug: str

	class Config:
		from_attributes = True


class TenderBase(BaseModel):
	title: str
	url: str
	description: Optional[str] = None
	published_at: Optional[datetime] = None
	source_id: int


class TenderOut(TenderBase):
	id: int
	created_at: datetime
	source: Optional[SourceOut] = None

	class Config:
		from_attributes = True


class TenderFilter(BaseModel):
	query: Optional[str] = None
	source_slug: Optional[str] = None
	date_from: Optional[datetime] = None
	date_to: Optional[datetime] = None
	limit: int = Field(default=100, ge=1, le=1000)
	offset: int = Field(default=0, ge=0)


class EmailRequest(BaseModel):
	recipient: EmailStr
	query: Optional[str] = None
	source_slug: Optional[str] = None
	date_from: Optional[datetime] = None
	date_to: Optional[datetime] = None
	limit: int = 100
	offset: int = 0


# User schemas
class UserBase(BaseModel):
	username: str
	email: EmailStr
	full_name: Optional[str] = None
	is_active: bool = True
	is_admin: bool = False


class UserCreate(UserBase):
	password: str


class UserUpdate(BaseModel):
	username: Optional[str] = None
	email: Optional[EmailStr] = None
	full_name: Optional[str] = None
	password: Optional[str] = None
	is_active: Optional[bool] = None
	is_admin: Optional[bool] = None


class UserOut(UserBase):
	id: int
	created_at: datetime
	last_login: Optional[datetime] = None

	class Config:
		from_attributes = True


class UserLogin(BaseModel):
	username: str
	password: str


class Token(BaseModel):
	access_token: str
	token_type: str


class TokenData(BaseModel):
	username: Optional[str] = None
