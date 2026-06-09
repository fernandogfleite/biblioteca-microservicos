"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { registerUser } from "@/lib/apiClient";
import UserBadge from "@/app/components/UserBadge";

export default function RegistroPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    cpf: "",
    password: "",
  });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResult(null);
    setBusy(true);

    try {
      const response = await registerUser(form);
      if (response?.success) {
        setResult({ ok: true, message: "Conta criada com sucesso! Faca login." });
        setTimeout(() => router.push("/login"), 1500);
      } else {
        setResult({ ok: false, message: response?.message || "Falha ao cadastrar." });
      }
    } catch (err) {
      setResult({ ok: false, message: err.message || "Falha ao cadastrar." });
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
        <Link className="nav-chip" href="/login">
          Login
        </Link>
        <UserBadge />
      </nav>

      <header className="hero-panel">
        <span className="kicker">Novo usuario</span>
        <h1>Cadastro</h1>
        <p>Crie sua conta para acessar o sistema de biblioteca.</p>
      </header>

      <main className="layout-grid" style={{ maxWidth: "420px", margin: "0 auto" }}>
        <section className="surface-card">
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              Nome completo
              <input
                type="text"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                required
              />
            </label>
            <label>
              E-mail
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
                required
              />
            </label>
            <label>
              CPF (somente numeros)
              <input
                type="text"
                name="cpf"
                value={form.cpf}
                onChange={handleChange}
                placeholder="00000000000"
                maxLength={14}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                autoComplete="new-password"
                required
              />
            </label>
            <button className="action-button" type="submit" disabled={busy}>
              {busy ? "Cadastrando..." : "Criar conta"}
            </button>
          </form>

          {result && (
            <div className={`result-box ${result.ok ? "ok" : "error"}`}>
              {result.message}
            </div>
          )}

          <p style={{ marginTop: "1rem", fontSize: "0.875rem" }}>
            Ja tem conta?{" "}
            <Link href="/login" style={{ color: "var(--color-accent, #6366f1)" }}>
              Faca login
            </Link>
          </p>
        </section>
      </main>
    </div>
  );
}
