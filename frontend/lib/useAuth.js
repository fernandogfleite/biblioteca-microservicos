"use client";

import { useEffect, useState } from "react";

/**
 * Returns the current authenticated user from localStorage.
 *
 * @returns {{ user: object|null, isAdmin: boolean, isLoggedIn: boolean }}
 */
export function useAuth() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("auth_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {
      // malformed data – ignore
    }
  }, []);

  return {
    user,
    isLoggedIn: Boolean(user),
    isAdmin: user?.role === "ADMIN",
  };
}
