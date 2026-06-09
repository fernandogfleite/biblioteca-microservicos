const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api";

function buildPath(path) {
  return `${API_PREFIX}${path}`;
}

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);

  const token = getToken();
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const response = await fetch(buildPath(path), {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...(options.headers || {}),
      },
      signal: controller.signal,
      cache: "no-store",
    });

    const data = await response.json().catch(() => ({
      success: false,
      message: "Resposta invalida do servidor.",
    }));

    if (!response.ok) {
      const message = data?.message || "Falha ao processar requisicao.";
      throw new Error(message);
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Tempo limite excedido para resposta da API.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export function login(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function registerUser(payload) {
  return request("/usuarios", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Users ─────────────────────────────────────────────────────────────────────

export function listUsers() {
  return request("/usuarios");
}

export function getUser(userId) {
  return request(`/usuarios/${userId}`);
}

export function updateUser(userId, payload) {
  return request(`/usuarios/${userId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteUser(userId) {
  return request(`/usuarios/${userId}`, { method: "DELETE" });
}

export function getUserLoanHistory(userId) {
  return request(`/usuarios/${userId}/historico-emprestimos`);
}

// ── Books ─────────────────────────────────────────────────────────────────────

export function createBook(payload) {
  return request("/livros", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listBooks(filters = {}) {
  const params = new URLSearchParams();
  if (filters.titulo) params.set("titulo", filters.titulo);
  if (filters.autor) params.set("autor", filters.autor);
  if (filters.categoria) params.set("categoria", filters.categoria);
  if (filters.disponivel !== undefined && filters.disponivel !== "")
    params.set("disponivel", String(filters.disponivel));
  const qs = params.toString();
  return request(`/livros${qs ? `?${qs}` : ""}`);
}

export function listAvailableBooks() {
  return request("/livros/disponiveis");
}

export function getBookLoanHistory(bookId) {
  return request(`/livros/${bookId}/historico-emprestimos`);
}

// ── Loans ─────────────────────────────────────────────────────────────────────

export function createLoan(payload) {
  return request("/emprestimos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listLoans() {
  return request("/emprestimos");
}

export function listOpenLoans() {
  return request("/emprestimos/abertos");
}

export function returnLoan(payload) {
  return request("/devolucoes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createReservation(payload) {
  return request("/reservas", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listReservations() {
  return request("/reservas");
}

export function listPendingReservations() {
  return request("/reservas/pendentes");
}

export function cancelReservation(payload) {
  return request("/reservas/cancelar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Recommendations ───────────────────────────────────────────────────────────

export function getRecommendations(categoria) {
  return request(`/recomendacoes/${encodeURIComponent(categoria)}`);
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export function getDashboard() {
  return request("/dashboard");
}


export function requestRecommendations(category) {
  const encodedCategory = encodeURIComponent(category);
  return request(`/recomendacoes/${encodedCategory}`);
}