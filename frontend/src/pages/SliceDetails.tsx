import { Button, Col, Form, Input, Notification, Panel, Row } from "@canonical/react-components";
import type { SliceDetail } from "../types/slice";
import { useFetchData } from "../hooks/useFetchData";
import { useNavigate, useParams } from "react-router-dom";
import { EditorialSliceForm } from "../components/EditorialSliceForm/EditorialSliceForm";
import { SnapCard } from "../components/SnapCard/SnapCard";
import { useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";


export function SliceDetails() {
    const { id } = useParams<{ id: string }>();

    const navigate = useNavigate();
    const { error, data, refetch } = useFetchData<SliceDetail>(`/api/editorial_slice/${id}`);
    const [successText, setSuccessText] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const { sendRequest, error: operationError } = useApi();

    useEffect(() => {
        setSearchTerm("");
        setSuccessText("");
    }, [operationError])

    const handleUpdate = async (name: string, description: string) => {
        await sendRequest(`/api/editorial_slice/${id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name,
                description
            }),
        });

        await refetch();
        setSuccessText(`'${searchTerm}' added to the '${id}'.`);
    }

    const handleSearch = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        await sendRequest(
            `/api/editorial_slice/${id}/snaps`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: searchTerm
            }),
        });
        await refetch();
        setSuccessText(`'${searchTerm}' added to the '${id}'.`);
        setSearchTerm("");
    }

    const handleDeleteSlice = async () => {
        await sendRequest(`/api/editorial_slice/${id}`, {
            method: "DELETE",
        });
        navigate("/v2/dashboard/editorial_slices", { replace: true });
    }

    const handleDeleteSnap = async (snapName: string) => {
        await sendRequest(`/api/editorial_slice/${id}/remove_snap`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: snapName
            }),
        });
        await refetch();
        setSuccessText(`'${snapName}' deleted from the '${id}'.`);
    }

    return <Panel
        title={data ? `'${data.name}' slice details` : "Slice details"}
        controls={
            <Button className="u-no-margin--bottom" appearance="negative" onClick={handleDeleteSlice}>Delete Slice</Button>
        }
    >
        {successText && <Row>
            <Col size={12}>
                <Notification severity="positive">
                    {successText}
                </Notification>
            </Col>
        </Row>}

        {error || operationError && <Row>
            <Col size={12}>
                <Notification severity="negative">
                    {error || operationError}
                </Notification>
            </Col>
        </Row>}

        <Row>
            <Col size={4}>
                <h4>Details</h4>
                <EditorialSliceForm buttonLabel="Update" onSubmit={handleUpdate} initialName={data ? data.name : ""} initialDescription={data ? data.description : ""} />
            </Col>
            <Col size={8}>
                <h4>Snaps</h4>

                <Form inline onSubmit={handleSearch}>
                    <Input type="text" id="snap-search" name="snapName" autoComplete="off" placeholder="Enter snap name" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                    <Button appearance="positive" type="submit">Add Snap</Button>
                </Form>

                <ul className="p-list" style={{ maxHeight: "650px", overflow: "scroll" }}>
                    {
                        data && data.snaps.map(snap => <SnapCard
                            key={snap.snap_id}
                            snap={snap}
                            actionButton={
                                <Button
                                    appearance="negative"
                                    hasIcon
                                    onClick={() => handleDeleteSnap(snap.name)}
                                >
                                    <i className="p-icon--delete is-dark"></i>
                                    <span>Remove</span>
                                </Button>
                            }
                        />)
                    }

                </ul>
            </Col>
        </Row>
    </Panel>
}