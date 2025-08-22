import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import { ExternalRedirect, Layout } from "./components";
import NotFound from "./pages/NotFound";

const OLD_PATHS = [
  "excluded_snaps",
  "editorial_slices",
  "settings",
]

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/v2/dashboard/" element={<Dashboard />} />
        {OLD_PATHS.map((page) => (
          <Route
            key={page}
            path={`/v2/dashboard/${page}`}
            element={<ExternalRedirect to={`/dashboard/${page}`} />}

          />
        ))}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
