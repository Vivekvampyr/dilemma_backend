from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.vote import VoteIn, VoteOut
from app.services.vote import cast_post_vote, cast_comment_vote
from app.utils.deps import get_current_user

router = APIRouter()


@router.post("/posts/{post_id}", response_model=VoteOut)
async def vote_post(
    post_id: UUID,
    payload: VoteIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await cast_post_vote(db, current_user, post_id, payload.value)
    return VoteOut(
        vote_score=post.vote_score,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        user_vote=payload.value,
    )


@router.post("/comments/{comment_id}", response_model=VoteOut)
async def vote_comment(
    comment_id: UUID,
    payload: VoteIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = await cast_comment_vote(db, current_user, comment_id, payload.value)
    return VoteOut(
        vote_score=comment.vote_score,
        upvote_count=comment.upvote_count,
        downvote_count=comment.downvote_count,
        user_vote=payload.value,
    )