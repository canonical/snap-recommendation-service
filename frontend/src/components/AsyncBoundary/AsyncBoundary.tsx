import { Notification } from "@canonical/react-components";
import type { ReactNode } from "react";

export function AsyncBoundary({ label, error, children, loading }: { label: string; loading: boolean; children: ReactNode; error?: string }) {
    return (
        <>
            <h5>{label}</h5>
            {
                error && <Notification
                    severity="negative"
                    title="Error"
                >
                    {error}
                </Notification>
            }
            {
                loading && <div>Loading</div>
            }

            {children}
        </>
    )
}