import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import { Layout } from "./components";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/v2/dashboard" element={<Dashboard />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
