import { AppAside, Button, Col, Form, Icon, Notification, Panel, Row } from "@canonical/react-components";
import { useState } from "react";

export function CreateEditorialSliceAside({ close, refetch }: { close: () => void, refetch: () => Promise<void> }) {
    const [error, setError] = useState<string | null>(null)

    const createEditorialSlice = async (name: string, description: string) => {
        try {
            const response = await fetch("/api//editorial_slice", {
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
                <Row className="p-form__group">
                    <Col size={4}>
                        <label htmlFor="name" className="p-form__label">Slice name</label>
                    </Col>

                    <Col size={8}>
                        <div className="p-form__control">
                            <input type="text" id="name" name="name" autoComplete="name" />
                        </div>
                    </Col>
                </Row>
                <Row className="p-form__group">
                    <Col size={4}>
                        <label htmlFor="description" className="p-form__label">Description</label>
                    </Col>

                    <Col size={8}>
                        <div className="p-form__control">
                            <textarea id="description" name="description" rows={3}></textarea>
                        </div>
                    </Col>
                </Row>
                <Row>
                    <Col size={12}>
                        <button
                            className="p-button--positive u-float-right"
                            type="submit"
                            name="create"
                        >
                            Create
                        </button>
                    </Col>
                </Row>
            </Form>
        </Panel>
    </AppAside>
}