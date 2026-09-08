export type Publisher = {
    nickname: string | null;
    fullname: string | null;
    email: string | null;
    is_admin: boolean;
};

export type AccountResponse = {
    authenticated: boolean;
    publisher?: Publisher;
};
