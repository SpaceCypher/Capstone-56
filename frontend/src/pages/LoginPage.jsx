import { useState } from "react";
import { LogIn, Sparkles } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Input, Label } from "../components/ui/Forms";
import { Card, CardContent } from "../components/ui/Card";

export default function LoginPage() {
  const { login, authLoading, authError, setAuthMode, clearAuthError } = useStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    clearAuthError();
    setLocalError("");

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setLocalError("Email and password are required.");
      return;
    }

    await login({
      email: trimmedEmail,
      password,
    });
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <Card className="w-full max-w-md shadow-xl shadow-indigo-100/60 border-white relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-indigo-500 to-cyan-500" />
        <CardContent className="p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/30 border border-indigo-100 text-indigo-400 text-xs font-semibold mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              Welcome back
            </div>
            <h2 className="text-3xl font-extrabold text-white">Log In</h2>
            <p className="text-sm text-slate-400 mt-2">Continue your personalized learning journey.</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-2"
                required
              />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="mt-2"
                minLength={1}
                required
              />
            </div>

            {localError ? <p className="text-sm text-rose-600">{localError}</p> : null}
            {!localError && authError ? <p className="text-sm text-rose-600">{authError}</p> : null}

            <Button type="submit" className="w-full" size="lg" loading={authLoading}>
              {!authLoading && (
                <>
                  <LogIn className="w-4 h-4 mr-2" />
                  Log In
                </>
              )}
              {authLoading && "Logging in..."}
            </Button>
          </form>

          <p className="text-sm text-slate-400 text-center mt-6">
            New here?{" "}
            <button
              type="button"
              className="font-semibold text-indigo-400 hover:text-indigo-300"
              onClick={() => {
                clearAuthError();
                setAuthMode("signup");
              }}
            >
              Create an account
            </button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
