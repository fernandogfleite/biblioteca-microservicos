"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  cancelReservation,
  createLoan,
  createReservation,
  listAvailableBooks,
  listBooks,
  listLoans,
  listOpenLoans,
  listPendingReservations,
  returnLoan,
} from "@/lib/apiClient";
import UserBadge from "@/app/components/UserBadge";
import { requireText } from "@/lib/validators";

const initialLoanForm = {
  nome_usuario: "",
  livro_id: "",
};

const initialReturnForm = {
  emprestimo_id: "",
};

const initialReservationForm = {
  nome_usuario: "",
  livro_id: "",
};

function normalizeResult(payload) {
  return {
    ok: Boolean(payload?.success),
    message: payload?.success
      ? "Operacao concluida com sucesso."
      : payload?.message || "Falha ao processar requisicao.",
    payload,
  };
}

export default function EmprestimosPage() {
  const [loanForm, setLoanForm] = useState(initialLoanForm);
  const [returnForm, setReturnForm] = useState(initialReturnForm);
  const [reservationForm, setReservationForm] = useState(initialReservationForm);

  const [loans, setLoans] = useState([]);
  const [availableBooks, setAvailableBooks] = useState([]);
  const [unavailableBooks, setUnavailableBooks] = useState([]);
  const [openLoans, setOpenLoans] = useState([]);
  const [pendingReservations, setPendingReservations] = useState([]);

  const [busyAction, setBusyAction] = useState("");
  const [result, setResult] = useState(null);

  const runWithFeedback = async (actionName, run) => {
    setBusyAction(actionName);
    try {
      const data = await run();
      setResult(normalizeResult(data));
      return data;
    } catch (error) {
      setResult({
        ok: false,
        message: error.message || "Falha ao processar requisicao.",
      });
      return null;
    } finally {
      setBusyAction("");
    }
  };

  const onListLoans = async () => {
    const response = await runWithFeedback("list-loans", listLoans);
    if (response?.success) {
      setLoans(Array.isArray(response.data) ? response.data : []);
    }
  };

  const refreshSelectSources = async () => {
    setBusyAction("load-sources");
    try {
      const [
        booksResponse,
        allBooksResponse,
        openLoansResponse,
        pendingReservationsResponse,
      ] = await Promise.all([
        listAvailableBooks(),
        listBooks(),
        listOpenLoans(),
        listPendingReservations(),
      ]);

      const booksData = Array.isArray(booksResponse?.data) ? booksResponse.data : [];
      const allBooksData = Array.isArray(allBooksResponse?.data) ? allBooksResponse.data : [];
      const openLoansData = Array.isArray(openLoansResponse?.data) ? openLoansResponse.data : [];
      const pendingReservationsData = Array.isArray(pendingReservationsResponse?.data)
        ? pendingReservationsResponse.data
        : [];

      const unavailableBooksData = allBooksData.filter((book) => book.disponivel === false);

      setAvailableBooks(booksData);
      setUnavailableBooks(unavailableBooksData);
      setOpenLoans(openLoansData);
      setPendingReservations(pendingReservationsData);

      setLoanForm((prev) => {
        if (prev.livro_id && booksData.some((book) => book.id === prev.livro_id)) {
          return prev;
        }
        return {
          ...prev,
          livro_id: booksData[0]?.id || "",
        };
      });

      setReturnForm((prev) => {
        if (
          prev.emprestimo_id &&
          openLoansData.some((loan) => loan.id === prev.emprestimo_id)
        ) {
          return prev;
        }
        return {
          ...prev,
          emprestimo_id: openLoansData[0]?.id || "",
        };
      });

      setReservationForm((prev) => {
        if (
          prev.livro_id &&
          unavailableBooksData.some((book) => book.id === prev.livro_id)
        ) {
          return prev;
        }
        return {
          ...prev,
          livro_id: unavailableBooksData[0]?.id || "",
        };
      });
    } catch (error) {
      setResult({
        ok: false,
        message: error.message || "Falha ao carregar dados para os seletores.",
      });
    } finally {
      setBusyAction("");
    }
  };

  useEffect(() => {
    void onListLoans();
    void refreshSelectSources();
  }, []);

  const onCreateLoan = async (event) => {
    event.preventDefault();

    const nome_usuario = requireText(loanForm.nome_usuario);
    const livro_id = requireText(loanForm.livro_id);

    if (!nome_usuario || !livro_id) {
      setResult({
        ok: false,
        message:
          "Informe nome do usuario e selecione um livro disponivel para registrar o emprestimo.",
      });
      return;
    }

    const response = await runWithFeedback("create-loan", () =>
      createLoan({ nome_usuario, livro_id })
    );

    if (response?.success) {
      setLoanForm(initialLoanForm);
      await onListLoans();
      await refreshSelectSources();
    }
  };

  const onReturnLoan = async (event) => {
    event.preventDefault();

    const emprestimo_id = requireText(returnForm.emprestimo_id);
    if (!emprestimo_id) {
      setResult({
        ok: false,
        message: "Selecione um emprestimo em aberto para devolucao.",
      });
      return;
    }

    const response = await runWithFeedback("return-loan", () =>
      returnLoan({ emprestimo_id })
    );

    if (response?.success) {
      setReturnForm(initialReturnForm);
      await onListLoans();
      await refreshSelectSources();
    }
  };

  const onCreateReservation = async (event) => {
    event.preventDefault();

    const nome_usuario = requireText(reservationForm.nome_usuario);
    const livro_id = requireText(reservationForm.livro_id);

    if (!nome_usuario || !livro_id) {
      setResult({
        ok: false,
        message:
          "Informe nome do usuario e selecione um livro indisponivel para criar a reserva.",
      });
      return;
    }

    const response = await runWithFeedback("create-reservation", () =>
      createReservation({ nome_usuario, livro_id })
    );

    if (response?.success) {
      setReservationForm(initialReservationForm);
      await refreshSelectSources();
    }
  };

  const onCancelReservation = async (reserva_id) => {
    const cleanReservationId = requireText(reserva_id);

    if (!cleanReservationId) {
      setResult({
        ok: false,
        message: "Reserva invalida para cancelamento.",
      });
      return;
    }

    const response = await runWithFeedback("cancel-reservation", () =>
      cancelReservation({ reserva_id: cleanReservationId })
    );

    if (response?.success) {
      await refreshSelectSources();
    }
  };

  return (
    <div className="module-shell">
      <nav className="top-nav" aria-label="Navegacao principal">
        <Link className="nav-chip" href="/">
          Hub
        </Link>
        <Link className="nav-chip" href="/catalogo">
          Catalogo
        </Link>
        <Link className="nav-chip active" href="/emprestimos">
          Emprestimos
        </Link>
        <Link className="nav-chip" href="/recomendacoes">
          Recomendacoes
        </Link>
        <UserBadge />
      </nav>

      <header className="hero-panel">
        <span className="kicker">Modulo de emprestimos</span>
        <h1>Operacoes de Circulacao</h1>
        <p>Registre retiradas, devolucoes e reservas de livros indisponiveis.</p>
      </header>

      <main className="layout-grid">
        <section className="surface-card">
          <h2>Registrar emprestimo</h2>
          <form className="form-grid" onSubmit={onCreateLoan}>
            <label>
              Nome do usuario
              <input
                type="text"
                value={loanForm.nome_usuario}
                onChange={(event) =>
                  setLoanForm((prev) => ({ ...prev, nome_usuario: event.target.value }))
                }
                required
              />
            </label>

            <label>
              Livro disponivel
              <select
                value={loanForm.livro_id}
                onChange={(event) =>
                  setLoanForm((prev) => ({ ...prev, livro_id: event.target.value }))
                }
                required
                disabled={busyAction === "load-sources" || availableBooks.length === 0}
              >
                {availableBooks.length === 0 ? (
                  <option value="">Nenhum livro disponivel</option>
                ) : (
                  availableBooks.map((book) => (
                    <option key={book.id} value={book.id}>
                      {book.titulo}
                    </option>
                  ))
                )}
              </select>
            </label>

            <button
              className="action-button"
              type="submit"
              disabled={busyAction === "create-loan" || availableBooks.length === 0}
            >
              {busyAction === "create-loan" ? "Registrando..." : "Registrar emprestimo"}
            </button>
          </form>

          <h2 style={{ marginTop: 22 }}>Registrar devolucao</h2>
          <form className="form-grid" onSubmit={onReturnLoan}>
            <label>
              Emprestimo em aberto
              <select
                value={returnForm.emprestimo_id}
                onChange={(event) =>
                  setReturnForm((prev) => ({
                    ...prev,
                    emprestimo_id: event.target.value,
                  }))
                }
                required
                disabled={busyAction === "load-sources" || openLoans.length === 0}
              >
                {openLoans.length === 0 ? (
                  <option value="">Nenhum emprestimo em aberto</option>
                ) : (
                  openLoans.map((loan) => (
                    <option key={loan.id} value={loan.id}>
                      {loan.nome_usuario} - {loan.livro_titulo || "Livro nao identificado"}
                    </option>
                  ))
                )}
              </select>
            </label>

            <button
              className="ghost-button"
              type="submit"
              disabled={busyAction === "return-loan" || openLoans.length === 0}
            >
              {busyAction === "return-loan" ? "Registrando..." : "Confirmar devolucao"}
            </button>
          </form>

          <h2 style={{ marginTop: 22 }}>Reservar livro indisponivel</h2>
          <form className="form-grid" onSubmit={onCreateReservation}>
            <label>
              Nome do usuario
              <input
                type="text"
                value={reservationForm.nome_usuario}
                onChange={(event) =>
                  setReservationForm((prev) => ({
                    ...prev,
                    nome_usuario: event.target.value,
                  }))
                }
                required
              />
            </label>

            <label>
              Livro indisponivel
              <select
                value={reservationForm.livro_id}
                onChange={(event) =>
                  setReservationForm((prev) => ({
                    ...prev,
                    livro_id: event.target.value,
                  }))
                }
                required
                disabled={busyAction === "load-sources" || unavailableBooks.length === 0}
              >
                {unavailableBooks.length === 0 ? (
                  <option value="">Nenhum livro indisponivel</option>
                ) : (
                  unavailableBooks.map((book) => (
                    <option key={book.id} value={book.id}>
                      {book.titulo}
                    </option>
                  ))
                )}
              </select>
            </label>

            <button
              className="action-button"
              type="submit"
              disabled={
                busyAction === "create-reservation" || unavailableBooks.length === 0
              }
            >
              {busyAction === "create-reservation" ? "Reservando..." : "Criar reserva"}
            </button>
          </form>

          {result && (
            <div className={`result-box ${result.ok ? "ok" : "error"}`}>
              <div>{result.message}</div>
            </div>
          )}
        </section>

        <section className="surface-card">
          <h2>Emprestimos atuais</h2>
          <p className="helper-text">
            Atualize para verificar o status dos registros no servico.
          </p>

          <button
            className="ghost-button"
            onClick={onListLoans}
            disabled={busyAction === "list-loans"}
          >
            {busyAction === "list-loans" ? "Atualizando..." : "Atualizar lista"}
          </button>

          <button
            className="ghost-button"
            onClick={refreshSelectSources}
            disabled={busyAction === "load-sources"}
            style={{ marginLeft: 8 }}
          >
            {busyAction === "load-sources" ? "Sincronizando..." : "Atualizar seletores"}
          </button>

          <div className="list-wrap" aria-live="polite">
            {loans.length > 0 ? (
              loans.map((loan) => (
                <article
                  className="list-item"
                  key={loan.id || `${loan.livro_id}-${loan.nome_usuario}`}
                >
                  <h3>{loan.nome_usuario || "Usuario nao informado"}</h3>
                  <p>Livro: {loan.livro_titulo || "Livro nao identificado"}</p>
                  <span className="pill">{loan.status || "status indisponivel"}</span>
                </article>
              ))
            ) : (
              <p className="empty">Nenhum emprestimo carregado.</p>
            )}
          </div>

          <h2 style={{ marginTop: 28 }}>Reservas pendentes</h2>
          <p className="helper-text">
            Reservas criadas para livros que estavam indisponiveis.
          </p>

          <div className="list-wrap" aria-live="polite">
            {pendingReservations.length > 0 ? (
              pendingReservations.map((reservation) => (
                <article
                  className="list-item"
                  key={reservation.id || `${reservation.livro_id}-${reservation.nome_usuario}`}
                >
                  <h3>{reservation.nome_usuario || "Usuario nao informado"}</h3>
                  <p>Livro: {reservation.livro_titulo || "Livro nao identificado"}</p>
                  <span className="pill">{reservation.status || "status indisponivel"}</span>

                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => onCancelReservation(reservation.id)}
                    disabled={busyAction === "cancel-reservation"}
                    style={{ marginTop: 10 }}
                  >
                    {busyAction === "cancel-reservation"
                      ? "Cancelando..."
                      : "Cancelar reserva"}
                  </button>
                </article>
              ))
            ) : (
              <p className="empty">Nenhuma reserva pendente carregada.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}