from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.community import Community, CommunityMember, CommunityRole
from app.models.user import User
from app.schemas.community import CommunityCreate, CommunityUpdate, CommunityOut
from app.utils.deps import get_current_user
from app.utils.pagination import PageParams, PagedResponse

router = APIRouter()


@router.post("/", response_model=CommunityOut, status_code=201)
async def create_community(
    payload: CommunityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Community).where(Community.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Community name already taken")

    community = Community(**payload.model_dump(), creator_id=current_user.id)
    db.add(community)
    await db.flush()

    # creator auto-joins as admin
    db.add(CommunityMember(
        community_id=community.id,
        user_id=current_user.id,
        role=CommunityRole.admin,
    ))
    community.member_count = 1
    await db.flush()
    return community


@router.get("/", response_model=PagedResponse[CommunityOut])
async def list_communities(
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Community.id)))).scalar()
    result = await db.execute(
        select(Community)
        .order_by(Community.member_count.desc())
        .offset(params.offset)
        .limit(params.limit)
    )
    return PagedResponse.create(result.scalars().all(), total, params)


@router.get("/{name}", response_model=CommunityOut)
async def get_community(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Community).where(Community.name == name))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community


@router.post("/{name}/join", status_code=200)
async def join_community(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Community).where(Community.name == name))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    already = await db.execute(
        select(CommunityMember).where(
            CommunityMember.community_id == community.id,
            CommunityMember.user_id == current_user.id,
        )
    )
    if already.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")

    db.add(CommunityMember(community_id=community.id, user_id=current_user.id))
    community.member_count += 1
    return {"detail": "Joined successfully"}


@router.post("/{name}/leave", status_code=200)
async def leave_community(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Community).where(Community.name == name))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    result = await db.execute(
        select(CommunityMember).where(
            CommunityMember.community_id == community.id,
            CommunityMember.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=400, detail="Not a member")

    await db.delete(membership)
    community.member_count = max(0, community.member_count - 1)
    return {"detail": "Left successfully"}