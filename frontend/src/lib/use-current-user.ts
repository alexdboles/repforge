import { useQuery } from "@tanstack/react-query";
import { apiGet } from "./api";
import { getUserId } from "./profile";
import type { UserProfile } from "./types";

export function useCurrentUser() {
  const id = getUserId();
  return useQuery({
    queryKey: ["user", id],
    queryFn: () => apiGet<UserProfile>('/auth/me'),
    enabled: Boolean(id),
    retry: false,
  });
}

