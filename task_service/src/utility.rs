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

#[cfg(test)]
mod tests {
    use super::*;
    use jsonwebtoken::{EncodingKey, Header};

    #[test]
    fn decode_returns_claims_for_valid_token() {
        let claims = Claims {
            sub: "42".to_string(),
            exp: 4_102_444_800,
            token_type: "access".to_string(),
            is_service: false,
        };
        let secret = b"test-secret";
        let token = jsonwebtoken::encode(&Header::default(), &claims, &EncodingKey::from_secret(secret))
            .expect("token should be created");

        let decoded = decode(&token, &DecodingKey::from_secret(secret)).expect("token should decode");

        assert_eq!(decoded.sub, "42");
        assert_eq!(decoded.token_type, "access");
        assert!(!decoded.is_service);
    }

    #[test]
    fn decode_rejects_invalid_token() {
        let result = decode("broken-token", &DecodingKey::from_secret(b"test-secret"));

        assert!(result.is_err());
    }
}
