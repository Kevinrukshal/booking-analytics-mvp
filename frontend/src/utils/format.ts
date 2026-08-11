export const currency = (value?: number) => new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 }).format(value || 0);
export const percent = (value?: number) => new Intl.NumberFormat("en-GB", { style: "percent", maximumFractionDigits: 1 }).format(value || 0);
export const date = (value?: string) => value ? new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : "—";
export const compact = (value?: number) => new Intl.NumberFormat("en-GB", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);

