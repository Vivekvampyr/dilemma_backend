from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.post import Post, PostStatus
from app.models.vote import PostVote
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate, PostOut
from app.utils.deps import get_current_user, get_current_user_optional
from app.utils.pagination import PageParams, PagedResponse
from app.services.media import upload_post_media

router = APIRouter()


def _mask_author(post: Post) -> PostOut:
    """Return PostOut, hiding author if post is anonymous."""
    out = PostOut.model_validate(post)
    if post.is_anonymous:
        out.author = None
    return out


@router.post("/", response_model=PostOut, status_code=201)
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(**payload.model_dump(), author_id=current_user.id)
    db.add(post)
    await db.flush()
    return _mask_author(post)


@router.post("/{post_id}/media", response_model=PostOut)
async def attach_media(
    post_id: UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.media))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    await upload_post_media(db, post_id, files)
    await db.refresh(post)
    return _mask_author(post)


@router.get("/", response_model=PagedResponse[PostOut])
async def list_posts(
    community_id: UUID | None = None,
    sort: str = "hot",         # hot | new | top
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    q = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.media),
    ).where(Post.status == PostStatus.active)

    if community_id:
        q = q.where(Post.community_id == community_id)

    if sort == "new":
        q = q.order_by(Post.created_at.desc())
    elif sort == "top":
        q = q.order_by(Post.vote_score.desc())
    else:  # hot — score + recency
        q = q.order_by((Post.vote_score + Post.comment_count).desc(), Post.created_at.desc())

    total = (await db.execute(select(func.count(Post.id)).where(Post.status == PostStatus.active))).scalar()
    posts = (await db.execute(q.offset(params.offset).limit(params.limit))).scalars().all()

    items = []
    for post in posts:
        out = _mask_author(post)
        if current_user:
            vote_result = await db.execute(
                select(PostVote).where(PostVote.user_id == current_user.id, PostVote.post_id == post.id)
            )
            v = vote_result.scalar_one_or_none()
            out.user_vote = v.value if v else 0
        items.append(out)

    return PagedResponse.create(items, total, params)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.media))
        .where(Post.id == post_id, Post.status == PostStatus.active)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.view_count += 1   # increment view
    out = _mask_author(post)

    if current_user:
        v = (await db.execute(
            select(PostVote).where(PostVote.user_id == current_user.id, PostVote.post_id == post_id)
        )).scalar_one_or_none()
        out.user_vote = v.value if v else 0

    return out


@router.patch("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: UUID,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(post, field, val)

    await db.flush()
    return _mask_author(post)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")

    post.status = PostStatus.deleted