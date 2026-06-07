import Link from "next/link";

const modules = [
  {
    href: "/catalogo",
    title: "Catalogo",
    description: "Cadastre e consulte livros com fluxo dedicado para operacoes do acervo.",
    action: "Abrir modulo de catalogo",
  },
  {
    href: "/emprestimos",
    title: "Emprestimos",
    description: "Registre emprestimos, devolucoes e acompanhe o estado dos registros.",
    action: "Abrir modulo de emprestimos",
  },
  {
    href: "/recomendacoes",
    title: "Recomendacoes",
    description: "Busque livros por categoria em uma interface focada em descoberta.",
    action: "Abrir modulo de recomendacoes",
  },
];

export default function HomePage() {
  return (
    <div className="dashboard-shell">
      <header className="hero-panel">
        <span className="kicker">Plataforma modular</span>
        <h1>Biblioteca Online</h1>
        <p>
          Interface separada por contexto de negocio. Escolha o modulo e trabalhe com foco total em
          cada servico.
        </p>
      </header>

      <section className="module-grid" aria-label="Modulos disponiveis">
        {modules.map((module) => (
          <article key={module.href} className="module-card">
            <h2>{module.title}</h2>
            <p>{module.description}</p>
            <Link href={module.href} className="module-link">
              {module.action}
            </Link>
          </article>
        ))}
      </section>
    </div>
  );
}