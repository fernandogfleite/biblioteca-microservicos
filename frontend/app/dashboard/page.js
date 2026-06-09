"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getDashboard } from "@/lib/apiClient";
import UserBadge from "@/app/components/UserBadge";
import { useAuth } from "@/lib/useAuth";

function StatCard({ label, value, sub }) {
  return (
    <article className="surface-card" style={{ textAlign: "center" }}>
      <p className="kicker" style={{ marginBottom: "0.25rem" }}>
        {label}
      </p>
      <p style={{ fontSize: "2rem", fontWeight: 700, margin: 0 }}>{value ?? "—"}</p>
      {sub && <p style={{ fontSize: "0.8rem", color: "var(--color-muted, #6b7280)", marginTop: "0.25rem" }}>{sub}</p>}
    </article>
  );
}

export default function DashboardPage() {
  const { isAdmin } = useAuth();
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    setBusy(true);
    setError(null);
    try {
      const response = await getDashboard();
      if (response?.success) {
        setData(response.data);
      } else {
        setError(response?.message || "Falha ao carregar dashboard.");
      }
    } catch (err) {
      setError(err.message || "Falha ao carregar dashboard.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

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
        <Link className="nav-chip" href="/recomendacoes">
          Recomendacoes
        </Link>
        <Link className="nav-chip active" href="/dashboard">
          Dashboard
        </Link>
        <UserBadge />
      </nav>

      <header className="hero-panel">
        <span className="kicker">Administracao</span>
        <h1>Dashboard</h1>
        <p>Metricas agregadas de todos os servicos. Acesso restrito a administradores.</p>
      </header>

      {!isAdmin ? (
        <main>
          <div className="result-box error" style={{ marginTop: "1.5rem" }}>
            Acesso negado. Esta pagina e restrita a administradores.
          </div>
        </main>
      ) : (
      <main>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
          <button className="ghost-button" onClick={fetchDashboard} disabled={busy}>
            {busy ? "Atualizando..." : "Atualizar"}
          </button>
        </div>

        {error && (
          <div className="result-box error" style={{ marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        {data && (
          <>
            <h2>Acervo</h2>
            <div className="module-grid" style={{ marginBottom: "2rem" }}>
              <StatCard label="Total de livros" value={data.livros?.total} />
              <StatCard label="Livros disponiveis" value={data.livros?.disponiveis} />
              <StatCard label="Livros indisponiveis" value={data.livros?.indisponiveis} />
            </div>

            <h2>Usuarios</h2>
            <div className="module-grid" style={{ marginBottom: "2rem" }}>
              <StatCard label="Total de usuarios" value={data.usuarios?.total} />
            </div>

            <h2>Emprestimos</h2>
            <div className="module-grid" style={{ marginBottom: "2rem" }}>
              <StatCard label="Total de emprestimos" value={data.emprestimos?.total} />
              <StatCard label="Em aberto" value={data.emprestimos?.abertos} />
              <StatCard label="Devolvidos" value={data.emprestimos?.devolvidos} />
            </div>

            {data.livros_mais_emprestados?.length > 0 && (
              <>
                <h2>Livros mais emprestados</h2>
                <section className="surface-card" style={{ marginBottom: "2rem" }}>
                  <div className="list-wrap">
                    {data.livros_mais_emprestados.map((item, idx) => (
                      <article className="list-item" key={item.livro_id}>
                        <h3>
                          {idx + 1}. {item.titulo}
                        </h3>
                        <span className="pill">{item.total} emprestimo(s)</span>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            )}

            {data.usuarios_mais_ativos?.length > 0 && (
              <>
                <h2>Usuarios mais ativos</h2>
                <section className="surface-card">
                  <div className="list-wrap">
                    {data.usuarios_mais_ativos.map((item, idx) => (
                      <article className="list-item" key={item.identificador}>
                        <h3>
                          {idx + 1}. {item.identificador}
                        </h3>
                        <span className="pill">{item.total} emprestimo(s)</span>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </main>
      )}
    </div>
  );
}
