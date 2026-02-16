import { Button, Panel } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import { CreateEditorialSliceAside } from "../components";
import { AsyncBoundary } from "../components/AsyncBoundary/AsyncBoundary";
import { Link } from "react-router-dom";
import type { SliceListItem } from "../types/slice";
import { useAside } from "../hooks/useAside";

type EditorialSlicesResponse = SliceListItem[]

export function EditorialSlices() {
    const { error, loading, data, refetch } = useFetchData<EditorialSlicesResponse>('/api/editorial_slices');
    const { openAside, closeAside } = useAside();

    return <Panel
        title="Editoral Slices"
        controls={<Button
            appearance="positive"
            className="u-no-margin--bottom"
            onClick={() => openAside(
                <CreateEditorialSliceAside close={closeAside} refetch={refetch} />
            )}
        >
            Create slice
        </Button>}
    >
        <div className="u-fixed-width">
            <AsyncBoundary label="" loading={loading} error={error ? "An error occurred" : undefined}>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Description</th>
                            <th className="u-align--right"># of snaps</th>
                            <th className="u-align--right">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data && data.map((slice) => (
                            <tr key={slice.id}>
                                <th className="u-truncate">{slice.name}</th>
                                <td>{slice.description}</td>
                                <td className="u-align--right">{slice.snaps_count}</td>
                                <td className="u-align--right">
                                    <Link
                                        to={`/v2/dashboard/editorial_slice/${slice.id}`}
                                        className="p-button"
                                    >
                                        Edit
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </AsyncBoundary>
        </div>
    </Panel>
}