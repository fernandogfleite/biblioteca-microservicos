const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api";

function buildPath(path) {
  return `${API_PREFIX}${path}`;
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);

  try {
    const response = await fetch(buildPath(path), {
      ...options,
      headers: {
        "Content-Type": "application/json",
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

export function createBook(payload) {
  return request("/livros", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listBooks() {
  return request("/livros");
}

export function createLoan(payload) {
  return request("/emprestimos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listLoans() {
  return request("/emprestimos");
}

export function returnLoan(payload) {
  return request("/devolucoes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function requestRecommendations(category) {
  const encodedCategory = encodeURIComponent(category);
  return request(`/recomendacoes/${encodedCategory}`);
}