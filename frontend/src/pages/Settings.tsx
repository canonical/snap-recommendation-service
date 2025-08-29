import { Button, Col, Icon, Notification, Panel, Row } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import type { CollectorInfo } from "../types/collectorInfo";
import { useState } from "react";
import { AsyncBoundary } from "../components";

export function Settings() {
    const { error, loading, data, refetch } = useFetchData<CollectorInfo>('/api/settings');
    const [operationError, setOperationError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const formatDateTime = (date: string) => new Date(date).toLocaleString("en-GB", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    })

    const runPipeline = async (stepId: string) => {
        try {
            const response = await fetch("/api/run_pipeline_step", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    "step_name": stepId,
                }),
            })

            if (!response.ok) {
                throw new Error();
            }
            setOperationError(null);
            const parsedResult = await response.json();
            setMessage(parsedResult.message);
            await refetch();
        } catch {
            setOperationError("An error occurred");
            setMessage(null);
        }
    }

    return <Panel title="Settings">
        <div className="u-fixed-width">
            {message && <Notification severity="positive">{message}</Notification>}
            <AsyncBoundary label="Collector" loading={loading} error={error || operationError}>
                <Row className="p-form__group">
                    <Col size={4}>
                        <p>Last completed run:</p>
                    </Col>
                    <Col size={8}>
                        <p>{data ? formatDateTime(data.last_updated) : "-"}</p>
                    </Col>
                </Row>
                <hr />
                <div>
                    <table className="p-table">
                        <thead>
                            <tr>
                                <th>Step</th>
                                <th>Status</th>
                                <th>Last successful run</th>
                                <th>Last failed run</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                data?.pipeline_steps?.map(step =>
                                    <tr>
                                        <td>{step.name}</td>
                                        <td>
                                            <Icon name={step.success ? "success" : "error"} />
                                        </td>
                                        <td>
                                            {step.last_successful_run ? formatDateTime(step.last_successful_run) : "-"}
                                        </td>
                                        <td>
                                            {step.last_failed_run ? formatDateTime(step.last_failed_run) : "-"}
                                        </td>
                                        <td>
                                            <Button appearance="positive" onClick={() => runPipeline(step.id)}>Run now</Button>
                                        </td>
                                    </tr>
                                )
                            }
                        </tbody>
                    </table>
                </div>
            </AsyncBoundary>

        </div>
    </Panel>
}