import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import PostVisibility, sql_enum

if TYPE_CHECKING:
	from app.models.poi import Poi
	from app.models.event import Event
	from app.models.submission import Submission
	from app.models.user import User
	from app.models.quest import Quest


class Follow(Base):

	__tablename__ = "follows"

	follower_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		primary_key=True,
	)
	following_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		primary_key=True,
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	follower: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
	following: Mapped["User"] = relationship("User", foreign_keys=[following_id], back_populates="followers")


class Post(Base, UUIDMixin):
	__tablename__ = "posts"

	submission_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("submissions.id", ondelete="CASCADE"),
		nullable=True,
		unique=True,
	)
	quest_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("quests.id", ondelete="SET NULL"),
		nullable=True,
		index=True,
	)
	poi_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("pois.id", ondelete="SET NULL"),
		nullable=True,
		index=True,
	)
	event_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("events.id", ondelete="SET NULL"),
		nullable=True,
		index=True,
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

	caption: Mapped[str | None] = mapped_column(Text, nullable=True)
	location_name: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)
	visibility: Mapped[PostVisibility] = mapped_column(
		sql_enum(PostVisibility, name="post_visibility_enum"),
		nullable=False,
		default=PostVisibility.PUBLIC,
		server_default=PostVisibility.PUBLIC.value,
	)

	submission: Mapped["Submission | None"] = relationship("Submission", back_populates="post")
	quest: Mapped["Quest | None"] = relationship("Quest")
	poi: Mapped["Poi | None"] = relationship("Poi")
	event: Mapped["Event | None"] = relationship("Event", back_populates="posts")
	user: Mapped["User"] = relationship("User", back_populates="posts")
	likes: Mapped[list["Like"]] = relationship("Like", back_populates="post", cascade="all, delete-orphan")
	comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="post", cascade="all, delete-orphan")



class Like(Base):
	__tablename__ = "likes"

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		primary_key=True,
	)
	post_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("posts.id", ondelete="CASCADE"),
		primary_key=True,
	)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	user: Mapped["User"] = relationship("User", back_populates="likes")
	post: Mapped["Post"] = relationship("Post", back_populates="likes")


class Comment(Base, UUIDMixin):
	__tablename__ = "comments"

	post_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("posts.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	parent_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("comments.id", ondelete="SET NULL"),
		nullable=True,
		index=True,
	)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	post: Mapped["Post"] = relationship("Post", back_populates="comments")
	user: Mapped["User"] = relationship("User", back_populates="comments")
	parent: Mapped["Comment | None"] = relationship("Comment", remote_side="Comment.id", back_populates="replies")
	replies: Mapped[list["Comment"]] = relationship("Comment", back_populates="parent")
