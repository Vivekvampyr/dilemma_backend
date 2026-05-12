from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.comment import Comment, CommentStatus
from app.models.post import Post
from app.models.vote import CommentVote
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.utils.deps import get_current_user, get_current_user_optional
from app.utils.pagination import PageParams, PagedResponse

router = APIRouter()


def _mask_author(comment: Comment) -> CommentOut:
    out = CommentOut.model_validate(comment)
    if comment.is_anonymous:
        out.author = None
    return out


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=201)
async def add_comment(
    post_id: UUID,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.is_locked:
        raise HTTPException(status_code=403, detail="Post is locked")

    if payload.parent_id:
        parent = (await db.execute(
            select(Comment).where(Comment.id == payload.parent_id, Comment.post_id == post_id)
        )).scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    comment = Comment(
        **payload.model_dump(),
        author_id=current_user.id,
        post_id=post_id,
    )
    db.add(comment)
    post.comment_count += 1
    await db.flush()
    return _mask_author(comment)


@router.get("/{post_id}/comments", response_model=PagedResponse[CommentOut])
async def get_comments(
    post_id: UUID,
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    # fetch top-level comments only; replies are nested via selectinload
    q = (
        select(Comment)
        .options(selectinload(Comment.author), selectinload(Comment.replies).selectinload(Comment.author))
        .where(
            Comment.post_id == post_id,
            Comment.parent_id == None,
            Comment.status == CommentStatus.active,
        )
        .order_by(Comment.vote_score.desc())
    )
    total = (await db.execute(
        select(func.count(Comment.id)).where(Comment.post_id == post_id, Comment.parent_id == None)
    )).scalar()

    comments = (await db.execute(q.offset(params.offset).limit(params.limit))).scalars().all()

    items = []
    for c in comments:
        out = _mask_author(c)
        if current_user:
            v = (await db.execute(
                select(CommentVote).where(CommentVote.user_id == current_user.id, CommentVote.comment_id == c.id)
            )).scalar_one_or_none()
            out.user_vote = v.value if v else 0
        items.append(out)

    return PagedResponse.create(items, total, params)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: UUID,
    payload: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your comment")

    comment.body = payload.body
    await db.flush()
    return _mask_author(comment)


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your comment")

    comment.status = CommentStatus.deleted