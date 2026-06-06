"""Employee ORM model."""

from sqlalchemy import Integer, String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Employee(Base):
    """Represents a company employee."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    hire_date: Mapped[str] = mapped_column(String, nullable=False)  # ISO format: YYYY-MM-DD

    # Relationships
    department = relationship("Department", back_populates="employees")
    projects = relationship("Project", back_populates="employee")

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.name}', salary={self.salary})>"
