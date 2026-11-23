import { Button, Panel } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import { CreateSnapCollectionAside } from "../components";
import { AsyncBoundary } from "../components/AsyncBoundary/AsyncBoundary";
import { Link } from "react-router-dom";
import type { SnapCollectionListItem } from "../types/snapCollection";
import { useAside } from "../hooks/useAside";

type SnapCollectionsResponse = SnapCollectionListItem[];

export function SnapCollections() {
  const { error, loading, data, refetch } =
    useFetchData<SnapCollectionsResponse>("/api/snap-collections");
  const { openAside, closeAside } = useAside();

  return (
    <Panel
      title="Snap collections"
      controls={
        <Button
          appearance="positive"
          className="u-no-margin--bottom"
          onClick={() =>
            openAside(
              <CreateSnapCollectionAside
                close={closeAside}
                refetch={refetch}
              />,
            )
          }
        >
          Create collection
        </Button>
      }
    >
      <div className="u-fixed-width">
        <AsyncBoundary
          label=""
          loading={loading}
          error={error ? "An error occurred" : undefined}
        >
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
              {data &&
                data.map((collection) => (
                  <tr key={collection.id}>
                    <th className="u-truncate">{collection.name}</th>
                    <td>{collection.description}</td>
                    <td className="u-align--right">{collection.snaps_count}</td>
                    <td className="u-align--right">
                      <Link
                        to={`/dashboard/snap-collection/${collection.id}`}
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
  );
}
