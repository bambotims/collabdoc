from celery import shared_task


@shared_task
def export_document_stub(document_id: str, export_format: str = "html") -> dict[str, str]:
    return {
        "document_id": document_id,
        "format": export_format,
        "status": "stub",
    }
