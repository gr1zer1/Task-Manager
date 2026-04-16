mod db;
mod error;
mod models;
mod routes;
mod schemas;
mod state;
mod stream;
mod utility;

use std::time::Duration;

use axum::routing::get;

use crate::models::TaskModel;
use crate::routes::app;
use crate::state::AppState;
use crate::stream::publish_task_event;

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();

    let app_state: AppState = AppState::new().await;
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8002")
        .await
        .expect("Failed to bind to address");

    let app = app(&app_state);

    let state_for_bg = app_state.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(60));
        loop {
            interval.tick().await;
            let overdue_tasks = sqlx::query_as::<_, TaskModel>(
                "UPDATE tasks SET status = 'overdue'
             WHERE deadline < NOW()
             AND status NOT IN ('done', 'cancelled', 'overdue')
             RETURNING *",
            )
            .fetch_all(&state_for_bg.db_pool)
            .await;

            if let Ok(tasks) = overdue_tasks {
                for task in tasks {
                    //let _ = publish_task_event(&state_for_bg.rabbit, "overdue", task).await;
                }
            }
        }
    });

    axum::serve(listener, app).await.expect("Server Error");

    
}
