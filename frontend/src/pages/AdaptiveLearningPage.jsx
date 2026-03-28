import {
  Brain,
  ChevronLeft,
  RefreshCw,
  Send,
  Target,
  Timer,
} from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Badge, Label, Textarea } from "../components/ui/Forms";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";

function StateBadge({ state }) {
  const normalized = (state || "neutral").toLowerCase();
  const variantMap = {
    mastery: "success",
    improving: "primary",
    neutral: "default",
    struggling: "danger",
    guessing: "warning",
  };
  return (
    <Badge variant={variantMap[normalized] || "default"} className="capitalize px-3 py-1">
      {normalized}
    </Badge>
  );
}

export default function AdaptiveLearningPage() {
  const {
    adaptiveQuestion,
    adaptiveQuestionSet,
    adaptiveQuestionIndex,
    adaptiveFeedback,
    adaptiveSessionTopic,
    adaptiveSessionConcept,
    adaptiveAnswer,
    adaptiveError,
    loadingAdaptiveQuestion,
    loadingAdaptiveSubmit,
    setAdaptiveAnswer,
    cycleAdaptiveQuestion,
    handleAdaptiveSubmit,
    setView,
  } = useStore();

  return (
    <div className="max-w-4xl mx-auto py-6 animate-fade-in space-y-8">
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => setView("landing")}
          className="flex items-center text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors"
        >
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Home
        </button>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="uppercase tracking-wide text-[10px]">
            Topic: {adaptiveSessionTopic || adaptiveSessionConcept}
          </Badge>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={cycleAdaptiveQuestion}
            loading={loadingAdaptiveQuestion}
          >
            {!loadingAdaptiveQuestion && <RefreshCw className="w-4 h-4 mr-2" />}
            Refresh Question
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold tracking-tight text-white">Adaptive Practice Loop</h2>
        <p className="text-slate-400">
          Submit your answer and the AI will evaluate correctness, then return behavior-driven feedback and the next question.
        </p>
      </div>

      {adaptiveError ? (
        <Card className="border-rose-200 bg-rose-50/70">
          <CardContent className="py-4 text-sm text-rose-700">{adaptiveError}</CardContent>
        </Card>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <Card className="lg:col-span-3 shadow-xl shadow-black/50 border border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-400" /> Current Question
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {!adaptiveQuestion ? (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400">
                {loadingAdaptiveQuestion
                  ? "Loading adaptive question..."
                  : "No active question. Start a new adaptive session from home."}
              </div>
            ) : (
              <>
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                  <p className="text-sm text-slate-400 mb-2">
                    {adaptiveQuestion.topic} • Question {Math.min(adaptiveQuestionIndex + 1, adaptiveQuestionSet.length || 1)}/{adaptiveQuestionSet.length || 1}
                  </p>
                  <p className="text-white font-semibold leading-relaxed">{adaptiveQuestion.prompt}</p>
                </div>

                <div>
                  <Label htmlFor="adaptive-answer">Your Answer</Label>
                  <Textarea
                    id="adaptive-answer"
                    value={adaptiveAnswer}
                    onChange={(event) => setAdaptiveAnswer(event.target.value)}
                    placeholder="Write your reasoning, not just final output."
                    className="mt-2"
                  />
                </div>

                <Button
                  type="button"
                  onClick={handleAdaptiveSubmit}
                  loading={loadingAdaptiveSubmit}
                  className="w-full"
                  size="lg"
                >
                  {!loadingAdaptiveSubmit && <Send className="w-4 h-4 mr-2" />}
                  Submit Attempt
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 shadow-xl shadow-black/50 border border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-400" /> Adaptive Feedback
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {!adaptiveFeedback ? (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-5 text-sm text-slate-400">
                Submit your first attempt to get personalized feedback.
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">Detected State</p>
                  <StateBadge state={adaptiveFeedback.state} />
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm border-slate-800 p-4">
                  <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Reason</p>
                  <p className="text-sm text-slate-200 leading-relaxed">{adaptiveFeedback.reason}</p>
                </div>

                <div className="rounded-xl border border-indigo-800 bg-indigo-900/40 p-4">
                  <p className="text-xs uppercase tracking-wide text-indigo-400 mb-1">Explanation</p>
                  <p className="text-sm text-indigo-200 leading-relaxed">{adaptiveFeedback.explanation}</p>
                </div>

                <div className="rounded-xl border border-emerald-800 bg-emerald-900/40 p-4">
                  <p className="text-xs uppercase tracking-wide text-emerald-400 mb-1">Easier Practice</p>
                  <p className="text-sm text-emerald-200 leading-relaxed">{adaptiveFeedback.easier_question}</p>
                </div>

                <div className="rounded-xl border border-amber-800 bg-amber-900/40 p-4">
                  <p className="text-xs uppercase tracking-wide text-amber-400 mb-1">Next Step</p>
                  <p className="text-sm text-amber-200 leading-relaxed">{adaptiveFeedback.next_step}</p>
                </div>
              </>
            )}

            <Button type="button" variant="secondary" className="w-full" onClick={() => setView("dashboard")}>
              <Timer className="w-4 h-4 mr-2" /> Open Learning History
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
