
use axum::{Extension, Json};
use axum::extract::{Path, Request};
use axum::response::Response;
use axum::middleware::{Next, from_fn_with_state};
use axum::{Router, extract::State, routing::{get,patch,post}};
use jsonwebtoken::DecodingKey;
use crate::error::AppError;
use crate::models::TaskModel;
use crate::schemas::{TaskCreateSchema, TaskRequestSchema, TaskUpdateSchema};
use crate::utility::{decode, Claims};

use crate::db::*;

use crate::state::AppState;

pub fn app(state: &AppState) -> Router{
    Router::new()
    .route("/", get(|| async { "Hello, World!" }))
    .route("/done/{task_id}", patch(done_task))
    .route("/task", post(add_task).patch(update_task))
    .route_layer(from_fn_with_state(state.clone(), middleware_auth))
    .with_state(state.clone())

}

async fn middleware_auth(State(config):State<AppState>,mut req:Request,next:Next) -> Result<Response, AppError>{

    let token = req.headers()
                .get("Authorization")
                .map(|data|data.to_str().unwrap_or(""))
                .map(|data|data.strip_prefix("Bearer "))
                .ok_or(AppError::InternalServerError("".to_string()))?;


    let claims = decode(token.unwrap(), &DecodingKey::from_secret(config.jwt_config.jwt_secret.as_ref()))?;
    
    req.extensions_mut().insert(claims);


    Ok((next.run(req)).await)

}

async fn add_task(
    State(state):State<AppState>,
    Extension(claims):Extension<Claims>,
    Json(task):Json<TaskCreateSchema>
) -> Result<Json<TaskModel>, AppError>{

    let new_task = TaskRequestSchema{
        title: task.title,
        description: task.description,
        status: task.status,
        owner_id: claims.sub.parse::<i64>()
            .map_err(|_| AppError::InternalServerError("Invalid user ID in token".to_string()))?,
        assignee_id: task.assignee_id,
        deadline: task.deadline
    };
    
    Ok(Json(create_task(&state.db_pool, new_task).await?))
}

async fn update_task(State(state):State<AppState>,Json(task):Json<TaskUpdateSchema>) -> Result<Json<TaskModel>, AppError>{
       Ok(Json(update_task_by_id(&state.db_pool, task).await?))
}

async fn done_task(
    State(state):State<AppState>,
    Path(task_id): Path<i64>,
) -> Result<Json<TaskModel>, AppError>{

    Ok(Json(done_task_by_id(&state.db_pool, task_id).await?))
}