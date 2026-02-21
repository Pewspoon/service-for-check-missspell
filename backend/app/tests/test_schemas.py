import pytest
from pydantic import ValidationError

from models.user import BalanceReplenishRequest, MLPredictionRequest, UserCreate


def test_user_create_validation_rejects_short_username():
    with pytest.raises(ValidationError):
        UserCreate(
            username="ab",
            email="a@example.com",
            password="secret",
        )


def test_balance_replenish_request_validation_rejects_non_positive_amount():
    with pytest.raises(ValidationError):
        BalanceReplenishRequest(amount=0)


def test_ml_prediction_request_validation_requires_text_and_model_id():
    with pytest.raises(ValidationError):
        MLPredictionRequest(text="hi")  # missing model_id

    with pytest.raises(ValidationError):
        MLPredictionRequest(model_id=1)  # missing text

