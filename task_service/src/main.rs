mod state;
mod routes;
mod db;
mod models;
mod schemas;
mod error;
mod utility;

use std::time::Duration;


use crate::routes::app;
use crate::state::AppState;

#[tokio::main]
async fn main(){
    dotenvy::dotenv().ok();

    let app_state: AppState = AppState::new().await;
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8002")
        .await
        .expect("Failed to bind to address");
    
    let app= app(&app_state);
    
    tokio::spawn(async move {
    let mut interval = tokio::time::interval(Duration::from_secs(60));
    loop {
        interval.tick().await;
        sqlx::query(
            "UPDATE tasks SET status = 'overdue'
             WHERE deadline < NOW()
             AND status NOT IN ('done', 'cancelled', 'overdue')"
        )
        .execute(&app_state.db_pool)
        .await
        .ok();
        }
    });

    axum::serve(listener, app)
        .await
        .unwrap();


}
