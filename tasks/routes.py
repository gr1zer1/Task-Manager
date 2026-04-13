from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import db_helper, TaskModel
from tasks.schemas import TaskSchema, TaskResponseSchema

SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]

router = APIRouter(tags=["Tasks"])


@router.post("", response_model=TaskResponseSchema)
async def create_task(
    task: TaskSchema,
    user_id: int,
    session: SessionDep,
) -> TaskResponseSchema:
    new_task = TaskModel(
        title=task.title,
        description=task.description,
        is_completed=task.is_completed,
        user_id=user_id,
    )
    
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)
    
    return new_task


@router.get("", response_model=List[TaskResponseSchema])
async def get_user_tasks(
    user_id: int,
    session: SessionDep,
) -> List[TaskResponseSchema]:
    stmt = select(TaskModel).where(TaskModel.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponseSchema)
async def get_task(
    task_id: int,
    session: SessionDep,
) -> TaskResponseSchema:
    stmt = select(TaskModel).where(TaskModel.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponseSchema)
async def update_task(
    task_id: int,
    task_update: TaskSchema,
    session: SessionDep,
) -> TaskResponseSchema:
    stmt = select(TaskModel).where(TaskModel.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.title = task_update.title
    task.description = task_update.description
    task.is_completed = task_update.is_completed
    
    await session.commit()
    await session.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: SessionDep,
):
    stmt = select(TaskModel).where(TaskModel.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    await session.delete(task)
    await session.commit()
