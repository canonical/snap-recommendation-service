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
import NotAuthorized from "./pages/NotAuthorized";


export default function App() {
  return (
    <AsideProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/v2/dashboard" element={<Dashboard />} />
          <Route path="/v2/dashboard/excluded_snaps" element={<ExcludeSnaps />} />
          <Route path="/v2/dashboard/editorial_slices" element={<EditorialSlices />} />
          <Route path="/v2/dashboard/editorial_slice/:id" element={<SliceDetails />} />
          <Route path="/v2/dashboard/settings" element={<Settings />} />
          <Route path="/v2/dashboard/featured" element={<FeaturedSnaps />} />
          <Route path="/v2/dashboard/not-authorized" element={<NotAuthorized />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AsideProvider>
  );
}
