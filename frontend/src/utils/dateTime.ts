const DATE_TIME = new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
});

const DATE_TIME_WITH_SECONDS = new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
});

export function formatDateTime(value: string, withSeconds = false): string {
    return (withSeconds ? DATE_TIME_WITH_SECONDS : DATE_TIME).format(new Date(value));
}
