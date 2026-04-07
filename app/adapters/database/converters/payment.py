from app.adapters.database.tables import PaymentTable
from app.domain.entities.payment import Payment


def convert_payment_table_to_dto(
    *,
    result: PaymentTable,
) -> Payment:
    return Payment(
        id=result.id,
        amount=result.amount,
        currency=result.currency,
        description=result.description,
        meta_data=result.meta_data,
        status=result.status,
        idempotency_key=result.idempotency_key,
        webhook_url=result.webhook_url,
        processed_at=result.processed_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
