use std::sync::Arc;

use sqlx::{PgPool, postgres::PgPoolOptions};

use crate::stream::{RabbitMQ, init_rabbit};
#[derive(Debug,Clone) ]
pub struct AppState{

    pub db_pool: PgPool,
    pub jwt_config: JWTConfig,
    pub rabbit: Arc<RabbitMQ>,

}


#[derive(Debug, Clone)]
pub struct JWTConfig{
    pub jwt_secret: String,
}

impl AppState{
    pub async fn new() -> Self{
        let url = std::env::var("TASK_DATABASE_URL").expect("DATABASE_URL must be set");

        let rabbitmq_url = std::env::var("RABBITMQ_URL").expect("RABBITMQ_URL must be set");
        
        Self{
            db_pool: PgPoolOptions::new()
            .max_connections(10)
            .connect(&url)
            .await
            .expect("Failed to create database pool"),
            jwt_config: JWTConfig{
                jwt_secret: std::env::var("JWT_SECRET_KEY").expect("JWT_SECRET_KEY must be set"),
            },
            rabbit: Arc::new(init_rabbit(&rabbitmq_url).await.expect("Failed to connect to RabbitMQ")),

            
        }
    }
}