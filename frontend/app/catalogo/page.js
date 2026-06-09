"use client";

import Link from "next/link";
import { useState } from "react";

import { createBook, listBooks } from "@/lib/apiClient";
import { normalizeBookPayload } from "@/lib/validators";

const initialBookForm = {
  titulo: "",
  autor: "",
  categoria: "",
};

const initialFilters = {
  titulo: "",
  autor: "",
  categoria: "",
  disponivel: "",
};

function buildResult(payload) {
  return {
    ok: Boolean(payload?.success),
    message: payload?.success
      ? "Operacao concluida com sucesso."
      : payload?.message || "Falha ao processar requisicao.",
    payload,
  };
}

export default function CatalogoPage() {
  const [bookForm, setBookForm] = useState(initialBookForm);
  const [filters, setFilters] = useState(initialFilters);
  const [books, setBooks] = useState([]);
  const [busyAction, setBusyAction] = useState("");
  const [result, setResult] = useState(null);

  const runWithFeedback = async (actionName, run) => {
    setBusyAction(actionName);
    try {
      const data = await run();
      setResult(buildResult(data));
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

  const onListBooks = async () => {
    const activeFilters = {};
    if (filters.titulo.trim()) activeFilters.titulo = filters.titulo.trim();
    if (filters.autor.trim()) activeFilters.autor = filters.autor.trim();
    if (filters.categoria.trim()) activeFilters.categoria = filters.categoria.trim();
    if (filters.disponivel !== "") activeFilters.disponivel = filters.disponivel === "true";

    const response = await runWithFeedback("list-books", () => listBooks(activeFilters));
    if (response?.success) {
      setBooks(Array.isArray(response.data) ? response.data : []);
    }
  };

  const onSubmitBook = async (event) => {
    event.preventDefault();
    const payload = normalizeBookPayload(bookForm);

    if (!payload) {
      setResult({
        ok: false,
        message: "Preencha titulo, autor e categoria para cadastrar o livro.",
      });
      return;
    }

    const response = await runWithFeedback("create-book", () => createBook(payload));
    if (response?.success) {
      setBookForm(initialBookForm);
      await onListBooks();
    }
  };

  return (
    <div className="module-shell">
      <nav className="top-nav" aria-label="Navegacao principal">
        <Link className="nav-chip" href="/">
          Hub
        </Link>
        <Link className="nav-chip active" href="/catalogo">
          Catalogo
        </Link>
        <Link className="nav-chip" href="/emprestimos">
          Emprestimos
        </Link>
        <Link className="nav-chip" href="/recomendacoes">
          Recomendacoes
        </Link>
        <Link className="nav-chip" href="/dashboard">
          Dashboard
        </Link>
      </nav>

      <header className="hero-panel">
        <span className="kicker">Modulo de catalogo</span>
        <h1>Gestao de Acervo</h1>
        <p>Cadastre novos livros e visualize o acervo atual em uma tela dedicada.</p>
      </header>

      <main className="layout-grid">
        <section className="surface-card">
          <h2>Novo livro</h2>
          <p className="helper-text">Dados completos ajudam as recomendacoes e emprestimos.</p>
          <form className="form-grid" onSubmit={onSubmitBook}>
            <label>
              Titulo
              <input
                type="text"
                value={bookForm.titulo}
                onChange={(event) => setBookForm((prev) => ({ ...prev, titulo: event.target.value }))}
                required
              />
            </label>
            <label>
              Autor
              <input
                type="text"
                value={bookForm.autor}
                onChange={(event) => setBookForm((prev) => ({ ...prev, autor: event.target.value }))}
                required
              />
            </label>
            <label>
              Categoria
              <input
                type="text"
                value={bookForm.categoria}
                onChange={(event) =>
                  setBookForm((prev) => ({ ...prev, categoria: event.target.value }))
                }
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busyAction === "create-book"}>
              {busyAction === "create-book" ? "Cadastrando..." : "Cadastrar livro"}
            </button>
          </form>

          {result && (
            <div className={`result-box ${result.ok ? "ok" : "error"}`}>
              {result.message}
            </div>
          )}
        </section>

        <section className="surface-card">
          <h2>Buscar livros</h2>
          <p className="helper-text">Filtre por titulo, autor, categoria ou disponibilidade.</p>
          <div className="form-grid">
            <label>
              Titulo
              <input
                type="text"
                placeholder="ex: Dom Casmurro"
                value={filters.titulo}
                onChange={(e) => setFilters((prev) => ({ ...prev, titulo: e.target.value }))}
              />
            </label>
            <label>
              Autor
              <input
                type="text"
                placeholder="ex: Machado"
                value={filters.autor}
                onChange={(e) => setFilters((prev) => ({ ...prev, autor: e.target.value }))}
              />
            </label>
            <label>
              Categoria
              <input
                type="text"
                placeholder="ex: Romance"
                value={filters.categoria}
                onChange={(e) => setFilters((prev) => ({ ...prev, categoria: e.target.value }))}
              />
            </label>
            <label>
              Disponibilidade
              <select
                value={filters.disponivel}
                onChange={(e) => setFilters((prev) => ({ ...prev, disponivel: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="true">Disponivel</option>
                <option value="false">Indisponivel</option>
              </select>
            </label>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
            <button
              className="ghost-button"
              onClick={onListBooks}
              disabled={busyAction === "list-books"}
            >
              {busyAction === "list-books" ? "Buscando..." : "Buscar"}
            </button>
            <button
              className="ghost-button"
              onClick={() => { setFilters(initialFilters); setBooks([]); setResult(null); }}
            >
              Limpar
            </button>
          </div>

          <div className="list-wrap" aria-live="polite">
            {books.length > 0 ? (
              books.map((book) => (
                <article className="list-item" key={book.id || `${book.titulo}-${book.autor}`}>
                  <h3>{book.titulo || "Sem titulo"}</h3>
                  <p>{book.autor || "Autor nao informado"}</p>
                  <span className="pill">{book.categoria || "Sem categoria"}</span>
                  <span
                    className="pill"
                    style={{ background: book.disponivel ? "var(--color-success, #22c55e)" : "var(--color-error, #ef4444)", color: "#fff", marginLeft: "0.25rem" }}
                  >
                    {book.disponivel ? "Disponivel" : "Indisponivel"}
                  </span>
                </article>
              ))
            ) : (
              <p className="empty">Nenhum livro carregado ainda.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}


  const runWithFeedback = async (actionName, run) => {
    setBusyAction(actionName);
    try {
      const data = await run();
      setResult(buildResult(data));
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

  const onListBooks = async () => {
    const response = await runWithFeedback("list-books", listBooks);
    if (response?.success) {
      setBooks(Array.isArray(response.data) ? response.data : []);
    }
  };

  const onSubmitBook = async (event) => {
    event.preventDefault();
    const payload = normalizeBookPayload(bookForm);

    if (!payload) {
      setResult({
        ok: false,
        message: "Preencha titulo, autor e categoria para cadastrar o livro.",
      });
      return;
    }

    const response = await runWithFeedback("create-book", () => createBook(payload));
    if (response?.success) {
      setBookForm(initialBookForm);
      await onListBooks();
    }
  };

  return (
    <div className="module-shell">
      <nav className="top-nav" aria-label="Navegacao principal">
        <Link className="nav-chip" href="/">
          Hub
        </Link>
        <Link className="nav-chip active" href="/catalogo">
          Catalogo
        </Link>
        <Link className="nav-chip" href="/emprestimos">
          Emprestimos
        </Link>
        <Link className="nav-chip" href="/recomendacoes">
          Recomendacoes
        </Link>
      </nav>

      <header className="hero-panel">
        <span className="kicker">Modulo de catalogo</span>
        <h1>Gestao de Acervo</h1>
        <p>Cadastre novos livros e visualize o acervo atual em uma tela dedicada.</p>
      </header>

      <main className="layout-grid">
        <section className="surface-card">
          <h2>Novo livro</h2>
          <p className="helper-text">Dados completos ajudam as recomendacoes e emprestimos.</p>
          <form className="form-grid" onSubmit={onSubmitBook}>
            <label>
              Titulo
              <input
                type="text"
                value={bookForm.titulo}
                onChange={(event) => setBookForm((prev) => ({ ...prev, titulo: event.target.value }))}
                required
              />
            </label>
            <label>
              Autor
              <input
                type="text"
                value={bookForm.autor}
                onChange={(event) => setBookForm((prev) => ({ ...prev, autor: event.target.value }))}
                required
              />
            </label>
            <label>
              Categoria
              <input
                type="text"
                value={bookForm.categoria}
                onChange={(event) =>
                  setBookForm((prev) => ({ ...prev, categoria: event.target.value }))
                }
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busyAction === "create-book"}>
              {busyAction === "create-book" ? "Cadastrando..." : "Cadastrar livro"}
            </button>
          </form>

          {result && (
            <div className={`result-box ${result.ok ? "ok" : "error"}`}>
              {result.message}
            </div>
          )}
        </section>

        <section className="surface-card">
          <h2>Livros cadastrados</h2>
          <p className="helper-text">Atualize a lista para ver mudancas feitas por outros servicos.</p>
          <button className="ghost-button" onClick={onListBooks} disabled={busyAction === "list-books"}>
            {busyAction === "list-books" ? "Atualizando..." : "Atualizar lista"}
          </button>

          <div className="list-wrap" aria-live="polite">
            {books.length > 0 ? (
              books.map((book) => (
                <article className="list-item" key={book.id || `${book.titulo}-${book.autor}`}>
                  <h3>{book.titulo || "Sem titulo"}</h3>
                  <p>{book.autor || "Autor nao informado"}</p>
                  <span className="pill">{book.categoria || "Sem categoria"}</span>
                </article>
              ))
            ) : (
              <p className="empty">Nenhum livro carregado ainda.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
