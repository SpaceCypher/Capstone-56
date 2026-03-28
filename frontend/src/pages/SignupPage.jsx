import { useState } from "react";
import { UserPlus, Rocket } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Input, Label } from "../components/ui/Forms";
import { Card, CardContent } from "../components/ui/Card";

export default function SignupPage() {
  const { signup, authLoading, authError, setAuthMode, clearAuthError } = useStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    clearAuthError();
    setLocalError("");

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();

    if (!trimmedName || !trimmedEmail || !password || !confirmPassword) {
      setLocalError("All fields are required.");
      return;
    }
    if (trimmedName.length < 2) {
      setLocalError("Name must be at least 2 characters.");
      return;
    }
    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setLocalError("Passwords do not match.");
      return;
    }

    await signup({
      name: trimmedName,
      email: trimmedEmail,
      password,
    });
  }

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <Card className="w-full max-w-md shadow-xl shadow-cyan-100/60 border-white relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-cyan-500 to-indigo-500" />
        <CardContent className="p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-100 text-cyan-700 text-xs font-semibold mb-4">
              <Rocket className="w-3.5 h-3.5" />
              Start strong
            </div>
            <h2 className="text-3xl font-extrabold text-white">Create Account</h2>
            <p className="text-sm text-slate-400 mt-2">Set up your profile and unlock tailored learning paths.</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your full name"
                className="mt-2"
                minLength={2}
                required
              />
            </div>

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
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password"
                className="mt-2"
                minLength={6}
                required
              />
            </div>

            <div>
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                className="mt-2"
                minLength={6}
                required
              />
            </div>

            {localError ? <p className="text-sm text-rose-600">{localError}</p> : null}
            {!localError && authError ? <p className="text-sm text-rose-600">{authError}</p> : null}

            <Button type="submit" className="w-full" size="lg" loading={authLoading}>
              {!authLoading && (
                <>
                  <UserPlus className="w-4 h-4 mr-2" />
                  Create Account
                </>
              )}
              {authLoading && "Creating account..."}
            </Button>
          </form>

          <p className="text-sm text-slate-400 text-center mt-6">
            Already have an account?{" "}
            <button
              type="button"
              className="font-semibold text-indigo-400 hover:text-indigo-300"
              onClick={() => {
                clearAuthError();
                setAuthMode("login");
              }}
            >
              Log in
            </button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
