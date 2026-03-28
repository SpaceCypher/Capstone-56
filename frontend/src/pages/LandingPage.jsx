import { motion } from "framer-motion";
import { Sparkles, ArrowRight, BrainCircuit } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Input, Label } from "../components/ui/Forms";
import { Card, CardContent } from "../components/ui/Card";

export default function LandingPage() {
  const {
    topic,
    user,
    setTopic,
    setView,
    loadDashboard,
    loadUserTopics,
    handleGenerate,
    loadingGenerate,
    loadingDashboard,
    loadingUserTopics,
    error,
  } = useStore();

  async function handleOpenDashboard() {
    await Promise.all([
      loadDashboard(),
      loadUserTopics(),
    ]);
    setView("dashboard");
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] py-12 px-4 text-center">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-900/30 border border-indigo-700/50 text-indigo-300 text-sm font-medium mb-8 backdrop-blur-sm"
      >
        <Sparkles className="w-4 h-4" />
        <span>Smarter, Faster Learning</span>
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.1 }}
        className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-r from-indigo-300 via-cyan-300 to-indigo-300 bg-clip-text text-transparent"
      >
        AI-Powered <br className="hidden sm:block" /> Adaptive Learning
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="max-w-2xl text-lg text-slate-400 mb-10 leading-relaxed"
      >
        Let our AI assess your current knowledge level and generate a personalized, step-by-step learning plan tailored to your specific strengths and weaknesses.
      </motion.p>

      {user ? (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mb-6 text-sm text-slate-400"
        >
          Signed in as <span className="font-semibold text-indigo-300">{user.name}</span>
        </motion.p>
      ) : null}

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        className="w-full max-w-lg mx-auto group"
      >
        <Card className="shadow-xl shadow-indigo-500/20 border-indigo-700/30 relative group animate-scale-in">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-600 to-cyan-600 rounded-2xl opacity-20 group-hover:opacity-40 transition blur -z-10"></div>
          <CardContent className="p-8 relative rounded-2xl">
            <div className="flex flex-col gap-6 text-left">
              <div>
                <Label htmlFor="topic" className="text-base text-slate-300">What do you want to learn today?</Label>
                <div className="mt-2 relative">
                  <Input
                    id="topic"
                    placeholder="e.g., Recursion in Python, Machine Learning..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="pl-11 h-14 text-base"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && topic.trim() && !loadingGenerate) {
                        handleGenerate();
                      }
                    }}
                  />
                  <BrainCircuit className="w-5 h-5 text-slate-500 absolute left-4 top-1/2 -translate-y-1/2" />
                </div>
                {error && <p className="text-red-400 text-sm mt-2 font-medium">{error}</p>}
              </div>

              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button 
                  size="lg" 
                  className="w-full text-base font-semibold group" 
                  onClick={handleGenerate} 
                  loading={loadingGenerate}
                  disabled={!topic.trim()}
                >
                  {!loadingGenerate && (
                    <>
                      Start Diagnostic Assessment
                      <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                  {loadingGenerate && "AI is generating questions..."}
                </Button>
              </motion.div>

              <Button
                type="button"
                variant="secondary"
                className="w-full"
                onClick={handleOpenDashboard}
                loading={loadingDashboard || loadingUserTopics}
              >
                {loadingDashboard || loadingUserTopics ? "Loading history..." : "View Learning History"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
