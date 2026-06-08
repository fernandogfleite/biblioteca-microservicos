"""HTTP routes for the loan service."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, current_app, request

from .services import (
    cancel_reservation,
    create_loan,
    create_reservation,
    list_loans,
    list_open_loans,
    list_pending_reservations,
    list_reservations,
    return_loan,
)

loan_bp = Blueprint("emprestimos", __name__)


def json_response(
    *,
    success: bool,
    data: Any | None = None,
    message: str | None = None,
    status: int = 200,
) -> tuple[Dict[str, Any], int]:
    payload: Dict[str, Any] = {"success": success}
    if success:
        payload["data"] = data
    else:
        payload["message"] = message
    return payload, status


@loan_bp.get("/emprestimos")
def listar_emprestimos():
    db_path = current_app.config["DB_PATH"]
    loans = [loan.to_dict() for loan in list_loans(db_path)]
    return json_response(success=True, data=loans)


@loan_bp.get("/emprestimos/abertos")
def listar_emprestimos_abertos():
    db_path = current_app.config["DB_PATH"]
    loans = [loan.to_dict() for loan in list_open_loans(db_path)]
    return json_response(success=True, data=loans)


@loan_bp.post("/emprestimos")
def criar_emprestimo():
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    db_path = current_app.config["DB_PATH"]
    catalog_url = current_app.config["CATALOG_SERVICE_URL"]
    try:
        loan = create_loan(db_path, payload, catalog_url)
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=400)

    return json_response(success=True, data=loan.to_dict(), status=201)


@loan_bp.post("/devolucoes")
def devolver_emprestimo():
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    loan_id = payload.get("emprestimo_id")
    if loan_id is None or str(loan_id).strip() == "":
        return json_response(
            success=False,
            message="Campo obrigatorio ausente ou vazio: emprestimo_id.",
            status=400,
        )

    db_path = current_app.config["DB_PATH"]
    catalog_url = current_app.config["CATALOG_SERVICE_URL"]
    try:
        loan = return_loan(db_path, str(loan_id).strip(), catalog_url)
    except ValueError as exc:
        message = str(exc)
        status = 404 if "nao encontrado" in message else 400
        return json_response(success=False, message=message, status=status)

    return json_response(success=True, data=loan.to_dict())


@loan_bp.get("/reservas")
def listar_reservas():
    db_path = current_app.config["DB_PATH"]
    reservations = [reservation.to_dict() for reservation in list_reservations(db_path)]
    return json_response(success=True, data=reservations)


@loan_bp.get("/reservas/pendentes")
def listar_reservas_pendentes():
    db_path = current_app.config["DB_PATH"]
    reservations = [
        reservation.to_dict() for reservation in list_pending_reservations(db_path)
    ]
    return json_response(success=True, data=reservations)


@loan_bp.post("/reservas")
def criar_reserva():
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    db_path = current_app.config["DB_PATH"]
    catalog_url = current_app.config["CATALOG_SERVICE_URL"]

    try:
        reservation = create_reservation(db_path, payload, catalog_url)
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=400)

    return json_response(success=True, data=reservation.to_dict(), status=201)


@loan_bp.post("/reservas/cancelar")
def cancelar_reserva():
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    reservation_id = payload.get("reserva_id")
    if reservation_id is None or str(reservation_id).strip() == "":
        return json_response(
            success=False,
            message="Campo obrigatorio ausente ou vazio: reserva_id.",
            status=400,
        )

    db_path = current_app.config["DB_PATH"]

    try:
        reservation = cancel_reservation(db_path, str(reservation_id).strip())
    except ValueError as exc:
        message = str(exc)
        status = 404 if "nao encontrada" in message else 400
        return json_response(success=False, message=message, status=status)

    return json_response(success=True, data=reservation.to_dict())