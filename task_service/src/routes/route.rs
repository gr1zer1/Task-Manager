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
use crate::stream::publish_task_event;

use crate::db::*;

use crate::state::AppState;

pub fn app(state: &AppState) -> Router {
    let protected = Router::new()
        .route("/tasks/owner/{owner_id}", get(get_tasks_by_owner))
        .route("/tasks/assignee/{assignee_id}", get(get_tasks_by_assignee))
        .route("/done/{task_id}", patch(done_task))
        .route("/task", post(add_task).patch(update_task))
        .route_layer(from_fn_with_state(state.clone(), middleware_auth));

    Router::new()
        .route("/", get(|| async { "Hello, World!" })) 
        .merge(protected)
        .with_state(state.clone())
}

async fn middleware_auth(State(config):State<AppState>,mut req:Request,next:Next) -> Result<Response, AppError>{

    let header = req.headers()
    .get("Authorization")
    .ok_or(AppError::Unauthorized("Missing Authorization header".to_string()))?;

    let header_str = header.to_str()
        .map_err(|_| AppError::Unauthorized("Invalid header format".to_string()))?;

    let token = header_str
        .strip_prefix("Bearer ")
        .ok_or(AppError::Unauthorized("Invalid authorization scheme".to_string()))?;


    let claims = decode(token, &DecodingKey::from_secret(config.jwt_config.jwt_secret.as_ref()))?;
    
    req.extensions_mut().insert(claims);


    Ok((next.run(req)).await)

}

fn authorize_user_access(claims: &Claims, requested_user_id: i64) -> Result<(), AppError> {
    if claims.is_service {
        return Ok(());
    }

    let user_id = claims
        .sub
        .parse::<i64>()
        .map_err(|_| AppError::Unauthorized("Invalid user ID in token".to_string()))?;

    if user_id != requested_user_id {
        return Err(AppError::Unauthorized("Access denied".to_string()));
    }

    Ok(())
}

async fn get_tasks_by_owner(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(owner_id): Path<i64>,
) -> Result<Json<Vec<TaskModel>>, AppError> {
    authorize_user_access(&claims, owner_id)?;
    Ok(Json(get_tasks_by_owner_id(&state.db_pool, owner_id).await?))
}

async fn get_tasks_by_assignee(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(assignee_id): Path<i64>,
) -> Result<Json<Vec<TaskModel>>, AppError> {
    authorize_user_access(&claims, assignee_id)?;
    Ok(Json(get_tasks_by_assignee_id(&state.db_pool, assignee_id).await?))
}

async fn add_task(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(task): Json<TaskCreateSchema>
) -> Result<Json<TaskModel>, AppError> {
    let new_task = TaskRequestSchema {
        title: task.title,
        description: task.description,
        status: task.status,
        owner_id: claims.sub.parse::<i64>()
            .map_err(|_| AppError::InternalServerError("Invalid user ID in token".to_string()))?,
        assignee_id: task.assignee_id,
        deadline: task.deadline
    };

    let created_task = create_task(&state, new_task).await?;
    publish_task_event(state.rabbit.as_ref(), "created", created_task.clone()).await?;

    Ok(Json(created_task))
}

async fn update_task(
    State(state): State<AppState>,
    Json(task): Json<TaskUpdateSchema>,
) -> Result<Json<TaskModel>, AppError> {
    let updated_task = update_task_by_id(&state.db_pool, task).await?;
    publish_task_event(state.rabbit.as_ref(), "updated", updated_task.clone()).await?;

    Ok(Json(updated_task))
}

async fn done_task(
    State(state):State<AppState>,
    Path(task_id): Path<i64>,
) -> Result<Json<TaskModel>, AppError>{
    let updated_task = done_task_by_id(&state.db_pool, task_id).await?;
    publish_task_event(state.rabbit.as_ref(), "updated", updated_task.clone()).await?;

    Ok(Json(updated_task))
}

#[cfg(test)]
mod tests {
    use super::authorize_user_access;
    use crate::error::AppError;
    use crate::utility::Claims;

    fn claims(sub: &str, is_service: bool) -> Claims {
        Claims {
            sub: sub.to_string(),
            exp: 4_102_444_800,
            token_type: "access".to_string(),
            is_service,
        }
    }

    #[test]
    fn authorize_user_access_allows_matching_user() {
        let result = authorize_user_access(&claims("7", false), 7);

        assert!(result.is_ok());
    }

    #[test]
    fn authorize_user_access_allows_service_account() {
        let result = authorize_user_access(&claims("service", true), 99);

        assert!(result.is_ok());
    }

    #[test]
    fn authorize_user_access_rejects_other_user() {
        let result = authorize_user_access(&claims("7", false), 8);

        match result {
            Err(AppError::Unauthorized(message)) => assert_eq!(message, "Access denied"),
            other => panic!("unexpected result: {:?}", other),
        }
    }
}
