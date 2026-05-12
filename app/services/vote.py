from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.vote import PostVote, CommentVote
from app.models.post import Post
from app.models.comment import Comment
from app.models.user import User


async def cast_post_vote(db: AsyncSession, user: User, post_id: UUID, value: int) -> Post:
    # load post
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check existing vote
    result = await db.execute(
        select(PostVote).where(PostVote.user_id == user.id, PostVote.post_id == post_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.value == value:
            # same vote → undo (delete)
            _adjust_post_counts(post, -existing.value)
            await db.delete(existing)
            _adjust_karma(user, "post", -existing.value)
        else:
            # flip vote
            _adjust_post_counts(post, -existing.value + value)
            _adjust_karma(user, "post", -existing.value + value)
            existing.value = value
    else:
        # new vote
        vote = PostVote(user_id=user.id, post_id=post_id, value=value)
        db.add(vote)
        _adjust_post_counts(post, value)
        _adjust_karma(user, "post", value)

    await db.flush()
    return post


async def cast_comment_vote(db: AsyncSession, user: User, comment_id: UUID, value: int) -> Comment:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    result = await db.execute(
        select(CommentVote).where(CommentVote.user_id == user.id, CommentVote.comment_id == comment_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.value == value:
            _adjust_comment_counts(comment, -existing.value)
            await db.delete(existing)
            _adjust_karma(user, "comment", -existing.value)
        else:
            _adjust_comment_counts(comment, -existing.value + value)
            _adjust_karma(user, "comment", -existing.value + value)
            existing.value = value
    else:
        vote = CommentVote(user_id=user.id, comment_id=comment_id, value=value)
        db.add(vote)
        _adjust_comment_counts(comment, value)
        _adjust_karma(user, "comment", value)

    await db.flush()
    return comment


def _adjust_post_counts(post: Post, delta: int):
    post.vote_score += delta
    if delta > 0:
        post.upvote_count += delta
    else:
        post.downvote_count += abs(delta)


def _adjust_comment_counts(comment: Comment, delta: int):
    comment.vote_score += delta
    if delta > 0:
        comment.upvote_count += delta
    else:
        comment.downvote_count += abs(delta)


def _adjust_karma(user: User, kind: str, delta: int):
    if kind == "post":
        user.post_karma += delta
    else:
        user.comment_karma += delta