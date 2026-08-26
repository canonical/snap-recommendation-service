import { AppAside, Notification, Panel } from "@canonical/react-components";
import { AsideCloseButton } from "../AsideCloseButton/AsideCloseButton";
import { EditorialSliceForm } from "../EditorialSliceForm/EditorialSliceForm";
import { useApi } from "../../hooks/useApi";

export function CreateEditorialSliceAside({ close, refetch }: { close: () => void, refetch: () => Promise<void> }) {
    const { sendRequest, error } = useApi();

    const createEditorialSlice = async (name: string, description: string) => {
        await sendRequest("/api/editorial_slice", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                "name": name,
                "description": description
            }),
        })
        await refetch();
        close();
    }

    return <AppAside>
        <Panel
            title="Create new editorial Slice"
            controls={<AsideCloseButton close={close} />}
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