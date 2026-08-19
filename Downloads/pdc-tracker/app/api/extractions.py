from flask import Blueprint, request, g
from app.utils.errors import error_response
from app.utils.jwt_required import jwt_required
from app.utils.rbac import require_role
from app.models.user import UserRole
from app.services import extraction_service

extractions_bp = Blueprint("extractions", __name__)


@extractions_bp.route("/api/extractions", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def trigger_extraction():
    data = request.get_json(silent=True) or {}
    upload_id = data.get("upload_id")

    if not upload_id:
        return error_response("VALIDATION_ERROR", "upload_id required", 422)

    company_id = g.current_user.company_id

    try:
        result = extraction_service.run_extraction(
            upload_id=int(upload_id),
            company_id=int(company_id),
            user_id=g.current_user.id,
        )
        return result, 200
    except ValueError as exc:
        return error_response("EXTRACTION_FAILED", str(exc), 422)
    except Exception:
        from flask import current_app
        current_app.logger.exception("Extraction pipeline error for upload_id=%s", upload_id)
        return error_response("EXTRACTION_FAILED", "Extraction pipeline failed", 500)


@extractions_bp.route("/api/extractions/pending", methods=["GET"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def list_pending():
    company_id = g.current_user.company_id
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    items, total = extraction_service.list_pending_reviews(company_id, page, per_page)
    return {
        "data": [item.to_dict() for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }, 200


@extractions_bp.route("/api/extractions/<int:review_id>", methods=["GET"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def get_review(review_id):
    review = extraction_service.get_review(review_id)
    if review is None or review.company_id != g.current_user.company_id:
        return error_response("NOT_FOUND", "Review not found", 404)
    return review.to_dict(), 200


@extractions_bp.route("/api/extractions/<int:review_id>/approve", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def approve_review(review_id):
    data = request.get_json(silent=True) or {}
    company_id = g.current_user.company_id
    corrected = data.get("corrected_fields", data.get("extracted_data", {}))
    try:
        doc_id = extraction_service.approve_review(
            review_id=review_id,
            corrected_fields=corrected,
            user_id=g.current_user.id,
            company_id=company_id,
        )
        return {"document_id": doc_id}, 200
    except ValueError as exc:
        return error_response("APPROVE_FAILED", str(exc), 422)


@extractions_bp.route("/api/extractions/<int:review_id>/reject", methods=["POST"])
@jwt_required
@require_role(UserRole.owner, UserRole.finance_manager)
def reject_review(review_id):
    data = request.get_json(silent=True) or {}
    company_id = g.current_user.company_id
    reason = (data.get("reason") or "rejected").strip()

    try:
        extraction_service.reject_review(
            review_id=review_id,
            reason=reason,
            user_id=g.current_user.id,
            company_id=company_id,
        )
        return {"status": "rejected"}, 200
    except ValueError as exc:
        return error_response("REJECT_FAILED", str(exc), 422)
