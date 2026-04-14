use serde::{Deserialize, Serialize};


#[derive(Debug, Serialize, Deserialize)]
pub struct TaskRequestSchema {
    
    pub title: String,
    pub description: Option<String>,
    pub status: String,
    pub owner_id: i64,
    pub assignee_id: Option<i64>,
    pub deadline: Option<chrono::NaiveDateTime>
    
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TaskCreateSchema{
    pub title: String,
    pub description: Option<String>,
    pub status: String,
    pub assignee_id: Option<i64>,
    pub deadline: Option<chrono::NaiveDateTime>
}



#[derive(Debug, Serialize, Deserialize)]
pub struct TaskUpdateSchema {
    pub id: i64,
    pub title: Option<String>,
    pub description: Option<String>,
    pub status: Option<String>,
    pub assignee_id: Option<i64>,
}