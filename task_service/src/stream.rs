use tokio::sync::Mutex;
use lapin::{BasicProperties, Channel, Connection, ConnectionProperties, options::*, types::FieldTable};
use crate::{error::AppError, models::TaskModel};

#[derive(Debug)]
pub struct RabbitMQ {
    pub conn: Connection,
    pub channel: Mutex<Channel>,  
}

pub async fn publish_task_event(
    rabbit: &RabbitMQ,
    event_type: &str,
    body: TaskModel,
) -> Result<(), AppError> {
    let req = serde_json::to_string(&body)?;
    let routing_key = format!("task.{}", event_type);

    let channel = rabbit.channel.lock().await;

    channel
        .basic_publish(
            "tasks".into(),
            routing_key.into(),
            BasicPublishOptions::default(),
            req.as_bytes(),
            BasicProperties::default()
                .with_content_type("application/json".into()),
        )
        .await?
        .await?;  

    Ok(())
}

pub async fn init_rabbit(url: &str) -> Result<RabbitMQ, AppError> {
    println!("Initializing RabbitMQ connection...");
    let mut retries = 5u32;
    let conn = loop {
    match tokio::time::timeout(
        tokio::time::Duration::from_secs(5),
        Connection::connect(url, ConnectionProperties::default())
    ).await {
        Ok(Ok(conn)) => break conn,
        Ok(Err(e)) => {
            if retries == 0 {
                return Err(AppError::from(e));
            }
            retries -= 1;
            println!("RabbitMQ not ready, retrying in 3s... ({} left)", retries);
            tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
        }
        Err(_) => {
            if retries == 0 {
                return Err(AppError::InternalServerError("RabbitMQ timeout".into()));
            }
            retries -= 1;
            println!("RabbitMQ timeout, retrying in 3s... ({} left)", retries);
            tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
        }
    }
    };
    println!("RabbitMQ connected");

    let channel = conn.create_channel().await?;
    tracing::info!("RabbitMQ channel created");

    channel.exchange_declare(
        "tasks".into(),
        lapin::ExchangeKind::Topic,
        ExchangeDeclareOptions {
            durable: true,
            ..Default::default()
        },
        FieldTable::default(),
    ).await?;
    tracing::info!("RabbitMQ exchange declared");

    Ok(RabbitMQ { conn, channel: Mutex::new(channel) })
}
pub async fn publish_task_created(
    rabbit: &RabbitMQ,
    body: TaskModel,
) -> Result<(), AppError> {
    publish_task_event(rabbit, "created", body).await
}