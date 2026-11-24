import { AppAside, Notification, Panel } from "@canonical/react-components";
import { AsideCloseButton } from "../AsideCloseButton/AsideCloseButton";
import { SnapCollectionForm } from "../SnapCollectionForm/SnapCollectionForm";
import { useApi } from "../../hooks/useApi";

export function CreateSnapCollectionAside({
  close,
  refetch,
}: {
  close: () => void;
  refetch: () => Promise<unknown>;
}) {
  const { sendRequest, error } = useApi();

  const createSnapCollection = async (name: string, description: string) => {
    const ok = await sendRequest("/api/snap-collection", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        description: description,
      }),
    });
    if (!ok) return;
    await refetch();
    close();
  };

  return (
    <AppAside>
      <Panel
        title="Create new collection"
        controls={<AsideCloseButton close={close} />}
      >
        <div className={"u-fixed-width"}>
          {error && (
            <Notification severity="negative" title="Error">
              {error}
            </Notification>
          )}
          <SnapCollectionForm
            onSubmit={createSnapCollection}
            buttonLabel="Create"
          />
        </div>
      </Panel>
    </AppAside>
  );
}
