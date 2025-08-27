import { AppAside, Button, Icon, Notification, Panel } from "@canonical/react-components";
import { useState } from "react";
import { EditorialSliceForm } from "../EditorialSliceForm/EditorialSliceForm";

function CloseAsideButton({ close }: { close: () => void }) {
    return <Button appearance="base" className="u-no-margin--bottom" hasIcon onClick={close}>
        <Icon name="close">Close</Icon>
    </Button>
}

export function CreateEditorialSliceAside({ close, refetch }: { close: () => void, refetch: () => Promise<void> }) {
    const [error, setError] = useState<string | null>(null)

    const createEditorialSlice = async (name: string, description: string) => {
        try {
            const response = await fetch("/api/editorial_slice", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    "name": name,
                    "description": description
                }),
            })

            if (!response.ok) {
                throw new Error("Failed to exclude snap.");
            }
            setError(null);
            await refetch();
            close();
        } catch {
            setError("An error occurred")
        }
    }

    return <AppAside>
        <Panel
            title="Create new editorial Slice"
            controls={<CloseAsideButton close={close} />}
        >
            <div className={"u-fixed-width"}>
                {
                    error && <Notification
                        severity="negative"
                        title="Error"
                    >
                        {error}
                    </Notification>
                }
                <EditorialSliceForm onSubmit={createEditorialSlice} buttonLabel="Create" />
            </div>
        </Panel>
    </AppAside>
}