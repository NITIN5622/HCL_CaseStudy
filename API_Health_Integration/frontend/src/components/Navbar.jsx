import { Activity } from "lucide-react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-white">
            <Activity size={18} />
          </span>
          <span className="leading-tight">
            <span className="block text-sm font-semibold text-slate-900">Brightline HR</span>
            <span className="block text-xs text-slate-500">Integration Health Monitor</span>
          </span>
        </Link>
      </div>
    </header>
  );
}
