import { Button, Form, Input } from "@canonical/react-components";

interface IProps {
    onSubmit: (name: string, description: string) => void,
    buttonLabel: string,
    initialName?: string,
    initialDescription?: string
}

export function EditorialSliceForm({ onSubmit, buttonLabel, initialName, initialDescription }: IProps) {
    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const formData = new FormData(event.currentTarget);
        onSubmit(formData.get("name") as string, formData.get("description") as string);
    }

    return (
        <Form
            stacked
            onSubmit={handleSubmit}
        >
            <Input type="text" id="name" label="Slice name" name={"name"} defaultValue={initialName} />
            <textarea id="description" name="description" rows={3} autoComplete="off" defaultValue={initialDescription}></textarea>
            <Button
                appearance="positive"
                className="u-float-right"
                type="submit"
                name="create"
            >
                {buttonLabel}
            </Button>
        </Form>
    )
}