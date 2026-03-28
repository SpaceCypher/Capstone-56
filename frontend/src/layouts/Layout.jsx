import { motion } from "framer-motion";
import { BrainCircuit, LogOut, UserRound } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";

export default function Layout({ children }) {
  const { user, logout, view, authMode, setView, setAuthMode } = useStore();
  const currentKey = user ? view : authMode;

  const handleLogoClick = () => {
    if (user) {
      setView("landing");
    } else {
      setAuthMode("login");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-950/80 border-b border-slate-800/50 shadow-lg shadow-black/50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <motion.div
            className="flex items-center gap-2 text-indigo-400 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={handleLogoClick}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <BrainCircuit className="w-8 h-8" />
            <h1 className="font-bold text-xl tracking-tight hidden sm:block bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              NeuroLearn AI
            </h1>
            <h1 className="font-bold text-xl tracking-tight sm:hidden bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              NeuroLearn
            </h1>
          </motion.div>

          {user ? (
            <motion.div
              className="flex items-center gap-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <p className="hidden sm:inline-flex items-center gap-2 text-sm font-medium text-slate-300 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700/50 backdrop-blur-sm">
                <UserRound className="w-4 h-4" />
                {user.name}
              </p>
              <Button type="button" variant="secondary" size="sm" onClick={logout}>
                <LogOut className="w-4 h-4 mr-1.5" />
                Logout
              </Button>
            </motion.div>
          ) : (
            <p className="text-sm font-medium text-slate-400 bg-slate-800/50 px-3 py-1 rounded-full border border-slate-700/50 backdrop-blur-sm">
              Adaptive Diagnostic
            </p>
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <motion.div
          key={currentKey}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {children}
        </motion.div>
      </main>

      <footer className="mt-20 border-t border-slate-800/50 py-8 text-center text-slate-500 text-sm">
        <p>AI-Powered Learning Platform &copy; 2026</p>
      </footer>
    </div>
  );
}
