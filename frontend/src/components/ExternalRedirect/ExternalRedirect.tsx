import { useEffect } from "react"

export function ExternalRedirect({ to }: { to: string }) {
    useEffect(() => {
        window.location.href = to
    }, [to])
    return null
}
