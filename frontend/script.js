const apiMeta = document.querySelector('meta[name="api-base"]');
const API_BASE = apiMeta?.content || "http://localhost:5000";
const responsesContainer = document.getElementById("respostas");

const appendResponse = (title, payload) => {
  const wrapper = document.createElement("div");
  wrapper.className = "response-item";
  const content = JSON.stringify(payload, null, 2);
  wrapper.innerHTML = `<strong>${title}</strong>${content}`;
  responsesContainer.prepend(wrapper);
};

const handleRequest = async (title, url, options = {}) => {
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    appendResponse(`${title} (HTTP ${response.status})`, data);
  } catch (error) {
    appendResponse(title, {
      success: false,
      message: "Falha ao comunicar com a API Gateway.",
    });
  }
};

document.getElementById("form-livro").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    titulo: document.getElementById("livro-titulo").value,
    autor: document.getElementById("livro-autor").value,
    categoria: document.getElementById("livro-categoria").value,
  };
  handleRequest("Cadastro de Livro", `${API_BASE}/livros`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
});

document
  .getElementById("btn-listar-livros")
  .addEventListener("click", () => {
    handleRequest("Lista de Livros", `${API_BASE}/livros`);
  });

document.getElementById("form-emprestimo").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    nome_usuario: document.getElementById("emprestimo-usuario").value,
    livro_id: document.getElementById("emprestimo-livro").value,
  };
  handleRequest("Cadastro de Emprestimo", `${API_BASE}/emprestimos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
});

document.getElementById("form-devolucao").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    emprestimo_id: document.getElementById("devolucao-id").value,
  };
  handleRequest("Registro de Devolucao", `${API_BASE}/devolucoes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
});

document
  .getElementById("form-recomendacao")
  .addEventListener("submit", (event) => {
    event.preventDefault();
    const categoria = document.getElementById("recomendacao-categoria").value;
    const encoded = encodeURIComponent(categoria);
    handleRequest("Recomendacoes", `${API_BASE}/recomendacoes/${encoded}`);
  });
