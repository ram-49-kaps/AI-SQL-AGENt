"""Project ORM model."""

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """Represents a company project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # Active, Completed, Delayed, Pending
    deadline: Mapped[str] = mapped_column(String, nullable=False)  # ISO format: YYYY-MM-DD

    # Relationship: many projects → one employee
    employee = relationship("Employee", back_populates="projects")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
