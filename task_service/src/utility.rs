use jsonwebtoken::{Algorithm, DecodingKey, Validation};
use serde::{Deserialize, Serialize};

use crate::error::AppError;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,
    pub exp: usize,
    #[serde(rename = "type")]
    pub token_type: String,
    #[serde(default)]
    pub is_service: bool,
}

pub fn decode(token: &str, key: &DecodingKey) -> Result<Claims, AppError> {
    let validation = Validation::new(Algorithm::HS256);
    let token_data = jsonwebtoken::decode::<Claims>(token, key, &validation)?;
    Ok(token_data.claims)
}
