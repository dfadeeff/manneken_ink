from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_parent, owned_learner
from ..db import get_db
from ..models import Learner, Parent
from ..schemas import LearnerIn, LearnerOut, LearnerPatch, TopicOut
from ..tutor import curriculum

router = APIRouter(prefix="/api", tags=["learners"])


@router.get("/learners", response_model=list[LearnerOut])
async def list_learners(
    parent: Parent = Depends(current_parent), db: AsyncSession = Depends(get_db)
):
    rows = await db.scalars(
        select(Learner).where(Learner.parent_id == parent.id).order_by(Learner.created_at)
    )
    return list(rows)


@router.post("/learners", response_model=LearnerOut, status_code=status.HTTP_201_CREATED)
async def create_learner(
    body: LearnerIn,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    learner = Learner(parent_id=parent.id, **body.model_dump())
    db.add(learner)
    await db.commit()
    await db.refresh(learner)
    return learner


@router.patch("/learners/{learner_id}", response_model=LearnerOut)
async def update_learner(
    learner_id: str,
    body: LearnerPatch,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    learner = await owned_learner(learner_id, parent, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(learner, field, value)
    await db.commit()
    await db.refresh(learner)
    return learner


@router.delete("/learners/{learner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learner(
    learner_id: str,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    learner = await owned_learner(learner_id, parent, db)
    await db.delete(learner)
    await db.commit()


@router.get("/learners/{learner_id}/topics", response_model=list[TopicOut])
async def learner_topics(
    learner_id: str,
    parent: Parent = Depends(current_parent),
    db: AsyncSession = Depends(get_db),
):
    learner = await owned_learner(learner_id, parent, db)
    return [
        TopicOut(id=t.id, subject=t.subject, label=curriculum.label(t, learner.language))
        for t in curriculum.for_class(learner.school_class)
    ]
