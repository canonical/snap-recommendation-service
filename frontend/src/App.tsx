import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import { Layout } from "./components";
import NotFound from "./pages/NotFound";
import { ExcludeSnaps } from "./pages/ExcludeSnaps";
import { EditorialSlices } from "./pages/EditorialSlices";
import { SliceDetails } from "./pages/SliceDetails";
import { AsideProvider } from "./contexts/AsideContext/AsideProvider";
import { Settings } from "./pages/Settings";
import { FeaturedSnaps } from "./pages/FeaturedSnaps";



export default function App() {
  return (
    <AsideProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/excluded_snaps" element={<ExcludeSnaps />} />
          <Route path="/dashboard/editorial_slices" element={<EditorialSlices />} />
          <Route path="/dashboard/editorial_slice/:id" element={<SliceDetails />} />
          <Route path="/dashboard/settings" element={<Settings />} />
          <Route path="/dashboard/featured" element={<FeaturedSnaps />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AsideProvider>
  );
}
