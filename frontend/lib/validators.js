export function requireText(value) {
  if (typeof value !== "string") {
    return "";
  }

  return value.trim();
}

export function normalizeBookPayload(bookForm) {
  const titulo = requireText(bookForm.titulo);
  const autor = requireText(bookForm.autor);
  const categoria = requireText(bookForm.categoria);

  if (!titulo || !autor || !categoria) {
    return null;
  }

  return {
    titulo,
    autor,
    categoria,
  };
}