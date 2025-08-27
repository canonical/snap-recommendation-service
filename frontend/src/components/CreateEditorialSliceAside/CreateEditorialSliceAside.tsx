import { AppAside, Button, Col, Form, Icon, Input, Notification, Panel, Row, Textarea } from "@canonical/react-components";
import { useState } from "react";

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

    const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const formData = new FormData(event.currentTarget);
        createEditorialSlice(formData.get("name") as string, formData.get("description") as string);
    }

    return <AppAside>
        <Panel
            title="Create new editorial Slice"
            controls={<>
                <Button appearance="base" className="u-no-margin--bottom" hasIcon onClick={close}>
                    <Icon name="close">Close</Icon>
                </Button>
            </>}
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
                <Form
                    stacked
                    onSubmit={onSubmit}
                >
                    <Input type="text" id="name" label="Slice name" name={"name"} />
                    <Textarea id="description" name="description" rows={3} label={"Description"} />
                    <Row>
                        <Col size={12}>
                            <Button
                                appearance="positive"
                                className="u-float-right"
                                type="submit"
                                name="create"
                            >
                                Create
                            </Button>
                        </Col>
                    </Row>
                </Form>
            </div>
        </Panel>
    </AppAside>
}