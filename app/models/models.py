from datetime import datetime

from typing import Optional,List
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Medspa(Base):
    __tablename__ = "medspas"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    services: Mapped[List["Service"]] = relationship("Service", back_populates="medspa", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="medspa", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("price > 0", name="services_price_positive"),
        CheckConstraint("duration > 0", name="services_duration_positive"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    medspa_id: Mapped[str] = mapped_column(String(26), ForeignKey("medspas.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # in cents per spec
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    medspa: Mapped["Medspa"] = relationship("Medspa", back_populates="services")


# Association table for appointment <-> services many-to-many
appointment_services_table = Table(
    "appointment_services",
    Base.metadata,
    Column("appointment_id", String(26), ForeignKey("appointments.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", String(26), ForeignKey("services.id", ondelete="RESTRICT"), primary_key=True),
)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'completed', 'canceled')",
            name="appointments_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    medspa_id: Mapped[str] = mapped_column(String(26), ForeignKey("medspas.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)  # in cents, derived from services
    total_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    medspa: Mapped["Medspa"] = relationship("Medspa", back_populates="appointments")
    services: Mapped[List["Service"]] = relationship(
        "Service",
        secondary=appointment_services_table,
        backref="appointments",
    )
