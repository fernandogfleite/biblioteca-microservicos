"use client";

import Link from "next/link";
import { useState } from "react";

import { createLoan, listLoans, returnLoan } from "@/lib/apiClient";
import { requireText } from "@/lib/validators";

const initialLoanForm = {
  nome_usuario: "",
  livro_id: "",
};

const initialReturnForm = {
  emprestimo_id: "",
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
  const [loans, setLoans] = useState([]);
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

  const onCreateLoan = async (event) => {
    event.preventDefault();

    const nome_usuario = requireText(loanForm.nome_usuario);
    const livro_id = requireText(loanForm.livro_id);

    if (!nome_usuario || !livro_id) {
      setResult({
        ok: false,
        message: "Informe nome do usuario e ID do livro para registrar o emprestimo.",
      });
      return;
    }

    const response = await runWithFeedback("create-loan", () => createLoan({ nome_usuario, livro_id }));
    if (response?.success) {
      setLoanForm(initialLoanForm);
      await onListLoans();
    }
  };

  const onReturnLoan = async (event) => {
    event.preventDefault();

    const emprestimo_id = requireText(returnForm.emprestimo_id);
    if (!emprestimo_id) {
      setResult({
        ok: false,
        message: "Informe um ID de emprestimo valido para devolucao.",
      });
      return;
    }

    const response = await runWithFeedback("return-loan", () => returnLoan({ emprestimo_id }));
    if (response?.success) {
      setReturnForm(initialReturnForm);
      await onListLoans();
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
      </nav>

      <header className="hero-panel">
        <span className="kicker">Modulo de emprestimos</span>
        <h1>Operacoes de Circulacao</h1>
        <p>Registre retiradas e devolucoes com rastreabilidade de cada emprestimo.</p>
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
              ID do livro
              <input
                type="text"
                value={loanForm.livro_id}
                onChange={(event) => setLoanForm((prev) => ({ ...prev, livro_id: event.target.value }))}
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busyAction === "create-loan"}>
              {busyAction === "create-loan" ? "Registrando..." : "Registrar emprestimo"}
            </button>
          </form>

          <h2 style={{ marginTop: 22 }}>Registrar devolucao</h2>
          <form className="form-grid" onSubmit={onReturnLoan}>
            <label>
              ID do emprestimo
              <input
                type="text"
                value={returnForm.emprestimo_id}
                onChange={(event) =>
                  setReturnForm((prev) => ({ ...prev, emprestimo_id: event.target.value }))
                }
                required
              />
            </label>
            <button className="ghost-button" type="submit" disabled={busyAction === "return-loan"}>
              {busyAction === "return-loan" ? "Registrando..." : "Confirmar devolucao"}
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
          <p className="helper-text">Atualize para verificar o status dos registros no servico.</p>
          <button className="ghost-button" onClick={onListLoans} disabled={busyAction === "list-loans"}>
            {busyAction === "list-loans" ? "Atualizando..." : "Atualizar lista"}
          </button>

          <div className="list-wrap" aria-live="polite">
            {loans.length > 0 ? (
              loans.map((loan) => (
                <article className="list-item" key={loan.id || `${loan.livro_id}-${loan.nome_usuario}`}>
                  <h3>{loan.nome_usuario || "Usuario nao informado"}</h3>
                  <p>Livro: {loan.livro_id || "-"}</p>
                  <span className="pill">{loan.status || "status indisponivel"}</span>
                </article>
              ))
            ) : (
              <p className="empty">Nenhum emprestimo carregado.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
