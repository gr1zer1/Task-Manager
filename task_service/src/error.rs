use axum::{Json, body::Body, http::{Response, StatusCode}, response::IntoResponse};



#[derive(Debug, thiserror::Error)]
#[allow(dead_code)]
pub enum AppError {
    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),
    #[error("Not found")]
    NotFound(),
    #[error("Validation error: {0}")]
    ValidationError(String),
    #[error("Internal server error: {0}")]
    InternalServerError(String),
    #[error("Unauthorized: {0}")]
    Unauthorized(String),
    #[error("JWT error: {0}")]
    JWTError(#[from] jsonwebtoken::errors::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response<Body> {
        let (status, message) = match self {
            AppError::NotFound() => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::ValidationError(msg) => (StatusCode::BAD_REQUEST, msg),
            AppError::DatabaseError(e) => {
                tracing::error!("DB error: {e}");
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".into())
            }
            AppError::InternalServerError(msg)   => {
                tracing::error!("Internal: {msg}");
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal error".into())
            }
            AppError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, msg),
            AppError::JWTError(e) => {
                tracing::error!("JWT error: {e}");
                (StatusCode::UNAUTHORIZED, "Invalid token".into())
            }
        };
        (status, Json(serde_json::json!({"error": message}))).into_response()
    }
}