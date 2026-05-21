import { Toaster } from "sonner";

export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-xl text-center space-y-3">
        <h1 className="text-3xl font-semibold text-brand-700">GiziGo</h1>
        <p className="text-slate-600">
          Pengoptimal rencana makan harian terhadap AKG Permenkes 28/2019.
        </p>
        <p className="text-slate-400 text-sm">
          UI lengkap dirakit di Phase 4 dan 5.
        </p>
      </div>
      <Toaster richColors position="top-right" />
    </div>
  );
}
