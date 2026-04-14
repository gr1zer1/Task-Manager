use serde::{Deserialize, Serialize};
use sqlx::prelude::FromRow;

#[derive(Clone, Debug, FromRow, Serialize, Deserialize)]
pub struct TaskModel{
    pub id:          i64,
    pub title:       String,
    pub description: Option<String>,
    pub status:      String, 
    pub owner_id:    i64,
    pub assignee_id: Option<i64>,
    pub created_at:  chrono::NaiveDateTime,
    pub updated_at:  chrono::NaiveDateTime,
    pub deadline:     Option<chrono::NaiveDateTime>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TaskStatus {
    Pending,
    InProgress,
    Done,
    Cancelled,
    Overdue
}

impl TaskStatus {
    pub fn as_str(&self) -> &str {
        match self {
            TaskStatus::Pending    => "pending",
            TaskStatus::InProgress => "in_progress",
            TaskStatus::Done       => "done",
            TaskStatus::Cancelled  => "cancelled",
            TaskStatus::Overdue    => "overdue",
        }
    }
}

impl TryFrom<&str> for TaskStatus {
    type Error = String;
    fn try_from(s: &str) -> Result<Self, Self::Error> {
        match s {
            "pending"     => Ok(TaskStatus::Pending),
            "in_progress" => Ok(TaskStatus::InProgress),
            "done"        => Ok(TaskStatus::Done),
            "cancelled"   => Ok(TaskStatus::Cancelled),
            "overdue"     => Ok(TaskStatus::Overdue),
            _             => Err(format!("unknown status: {s}")),
        }
    }
}