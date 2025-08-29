import { Button, Col, Icon, Panel, Row } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import type { CollectorInfo } from "../types/collectorInfo";

export function Settings() {
    const { error, loading, data, refetch } = useFetchData<CollectorInfo>('/api/settings');

    const formatDateTime = (date: string) => new Date(date).toLocaleString("en-GB", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    })

    const runPipeline = () => {

    }

    return <Panel title="Settings">
        <div className="u-fixed-width">
            <h5>Collector</h5>
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
                                        <Button appearance="positive">Run now</Button>
                                    </td>
                                    {/* <td>{step.last_successful_run.strftime("%Y-%m-%d %H:%M:%S") if step.last_successful_run else "-" }</td>
                                    <td>{step.last_failed_run.strftime("%Y-%m-%d %H:%M:%S") if step.last_failed_run else "-" }</td>
                                    <td>
                                        <form action="{{ url_for('dashboard.run_pipeline_step', step_name=step.id) }}"
                                            method="post">
                                            <button type="submit" className="p-button--positive">Run now</button>
                                        </form>
                                    </td> */}
                                </tr>
                            )
                        }
                    </tbody>
                </table>
            </div>
        </div>
    </Panel>
}