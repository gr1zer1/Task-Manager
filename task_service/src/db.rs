use sqlx::PgPool;

use crate::error::AppError;
use crate::models::TaskModel;
use crate::schemas::{TaskRequestSchema, TaskUpdateSchema};
use crate::state::AppState;
use crate::stream::publish_task_created;


pub async fn get_tasks_by_owner_id(pool: &PgPool, owner_id: i64) -> Result<Vec<TaskModel>, AppError> {
    sqlx::query_as::<_, TaskModel>("SELECT * FROM tasks WHERE owner_id = $1")
        .bind(owner_id)
        .fetch_all(pool)
        .await
        .map_err(|e| match e{
            sqlx::Error::RowNotFound => AppError::NotFound(),
            other => AppError::DatabaseError(other),
        })
}

pub async fn get_tasks_by_assignee_id(pool: &PgPool, assignee_id: i64) -> Result<Vec<TaskModel>, AppError> {
    sqlx::query_as::<_, TaskModel>("SELECT * FROM tasks WHERE assignee_id = $1")
        .bind(assignee_id)
        .fetch_all(pool)
        .await
        .map_err(|e| match e{
            sqlx::Error::RowNotFound => AppError::NotFound(),
            other => AppError::DatabaseError(other),
        })
}


pub async fn create_task(state: &AppState, task: TaskRequestSchema) -> Result<TaskModel, AppError> {
    let res = sqlx::query_as::<_, TaskModel>("INSERT INTO tasks (title, description, status, owner_id, assignee_id) VALUES ($1, $2, $3, $4, $5) RETURNING *")
        .bind(task.title)
        .bind(task.description)
        .bind(task.status)
        .bind(task.owner_id)
        .bind(task.assignee_id)
        .fetch_one(&state.db_pool)
        .await
        .map_err(|e| match e {
            sqlx::Error::RowNotFound => AppError::NotFound(),
            other => AppError::DatabaseError(other),
        })?;
    
    //publish_task_created(state.rabbit.as_ref(), res.clone()).await?;

    Ok(res)
}

pub async fn update_task_by_id(
    pool: &PgPool,
    task: TaskUpdateSchema,
) -> Result<TaskModel, AppError> {
    sqlx::query_as::<_, TaskModel>(
        "UPDATE tasks SET
            title       = COALESCE($1, title),
            description = COALESCE($2, description),
            status      = COALESCE($3, status),
            assignee_id = COALESCE($4, assignee_id),
            updated_at  = NOW()
         WHERE id = $5
         RETURNING *"
    )
    .bind(task.title)
    .bind(task.description)
    .bind(task.status)
    .bind(task.assignee_id)
    .bind(task.id)
    .fetch_one(pool)
    .await
    .map_err(|e| match e {
        sqlx::Error::RowNotFound => AppError::NotFound(),
        other => AppError::DatabaseError(other),
    })
}

pub async fn done_task_by_id(pool: &PgPool, task_id: i64) -> Result<TaskModel, AppError> {
    sqlx::query_as::<_, TaskModel>("UPDATE tasks SET status = 'done', updated_at = NOW() WHERE id = $1 RETURNING *")
        .bind(task_id)
        .fetch_one(pool)
        .await
        .map_err(|e| match e{
            sqlx::Error::RowNotFound => AppError::NotFound(),
            other => AppError::DatabaseError(other),
        })
}

