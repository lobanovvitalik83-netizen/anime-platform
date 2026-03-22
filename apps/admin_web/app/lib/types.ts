export type Permission = {
  id: number;
  key: string;
  description: string | null;
};

export type Role = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  permissions: Permission[];
};

export type User = {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  roles: Role[];
  permissions: Permission[];
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
