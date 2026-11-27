import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import IntegrationDetails from "./pages/IntegrationDetails.jsx";
import UploadPage from "./pages/UploadPage.jsx";

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/integrations/:id" element={<IntegrationDetails />} />
          <Route path="*" element={<p className="text-slate-500">Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
