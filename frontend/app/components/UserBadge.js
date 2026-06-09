"use client";

/**
 * UserBadge – shows the currently authenticated user in the nav bar.
 *
 * Reads `auth_user` and `auth_token` from localStorage.
 * Renders nothing when the user is not logged in.
 * Provides a logout button that clears local storage and redirects to /login.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function UserBadge() {
  const [user, setUser] = useState(null);
  const router = useRouter();

  useEffect(() => {
    try {
      const raw = localStorage.getItem("auth_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {
      // malformed data – ignore
    }
  }, []);

  if (!user) return null;

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    router.push("/login");
  };

  const label = user.full_name || user.email || "Usuário";
  const isAdmin = user.role === "ADMIN";

  return (
    <span className="user-badge" aria-label={`Logado como ${label}`}>
      <span className="user-badge__avatar" aria-hidden="true">
        {label.charAt(0).toUpperCase()}
      </span>
      <span className="user-badge__name">{label}</span>
      {isAdmin && <span className="user-badge__role">Admin</span>}
      <button className="user-badge__logout" onClick={handleLogout} type="button">
        Sair
      </button>
    </span>
  );
}
