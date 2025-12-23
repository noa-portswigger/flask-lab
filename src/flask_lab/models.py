# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from datetime import datetime, timezone
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = 'todo'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }
