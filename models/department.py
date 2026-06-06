"""Department ORM model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Department(Base):
    """Represents a company department."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    location: Mapped[str] = mapped_column(String, nullable=False)

    # Relationship: one department → many employees
    employees = relationship("Employee", back_populates="department")

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', location='{self.location}')>"
