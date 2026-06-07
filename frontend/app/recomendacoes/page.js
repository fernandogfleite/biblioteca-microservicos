"use client";

import Link from "next/link";
import { useState } from "react";

import { requestRecommendations } from "@/lib/apiClient";
import { requireText } from "@/lib/validators";

export default function RecomendacoesPage() {
  const [categoria, setCategoria] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const onRequestRecommendations = async (event) => {
    event.preventDefault();

    const normalizedCategory = requireText(categoria);
    if (!normalizedCategory) {
      setResult({
        ok: false,
        message: "Informe uma categoria valida para buscar recomendacoes.",
      });
      return;
    }

    setBusy(true);
    try {
      const response = await requestRecommendations(normalizedCategory);
      if (response?.success) {
        const list = Array.isArray(response.data) ? response.data : [];
        setRecommendations(list);
        setResult({
          ok: true,
          message: list.length
            ? "Recomendacoes carregadas com sucesso."
            : "Nenhum livro encontrado para esta categoria.",
          payload: response,
        });
      } else {
        setRecommendations([]);
        setResult({
          ok: false,
          message: response?.message || "Nao foi possivel buscar recomendacoes.",
        });
      }
    } catch (error) {
      setRecommendations([]);
      setResult({
        ok: false,
        message: error.message || "Falha ao processar requisicao.",
      });
    } finally {
      setBusy(false);
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
        <Link className="nav-chip" href="/emprestimos">
          Emprestimos
        </Link>
        <Link className="nav-chip active" href="/recomendacoes">
          Recomendacoes
        </Link>
      </nav>

      <header className="hero-panel">
        <span className="kicker">Modulo de recomendacoes</span>
        <h1>Descoberta por Categoria</h1>
        <p>Filtre o acervo por categoria em uma interface voltada para exploracao.</p>
      </header>

      <main className="layout-grid">
        <section className="surface-card">
          <h2>Buscar recomendacoes</h2>
          <p className="helper-text">Use categorias como romance, tecnologia ou historia.</p>
          <form className="form-grid" onSubmit={onRequestRecommendations}>
            <label>
              Categoria
              <input
                type="text"
                value={categoria}
                onChange={(event) => setCategoria(event.target.value)}
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busy}>
              {busy ? "Buscando..." : "Buscar"}
            </button>
          </form>

          {result && (
            <div className={`result-box ${result.ok ? "ok" : "error"}`}>
              <div>{result.message}</div>
            </div>
          )}
        </section>

        <section className="surface-card">
          <h2>Resultado da busca</h2>
          <div className="list-wrap" aria-live="polite">
            {recommendations.length > 0 ? (
              recommendations.map((book) => (
                <article className="list-item" key={book.id || `${book.titulo}-${book.autor}`}>
                  <h3>{book.titulo || "Sem titulo"}</h3>
                  <p>{book.autor || "Autor nao informado"}</p>
                  <span className="pill">{book.categoria || "Sem categoria"}</span>
                </article>
              ))
            ) : (
              <p className="empty">Nenhuma recomendacao carregada.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
