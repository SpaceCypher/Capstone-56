import { Brain, Target, AlertTriangle, Zap, CheckCircle, BookOpen, Navigation, RotateCcw, Gauge, ListChecks } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Forms";

export default function ResultPage() {
  const {
    topic,
    evaluation,
    learningPlan,
    aiSource,
    questionSource,
    stageSources,
    stageReasons,
    resumeMessage,
    resetStore,
    setView,
    startAdaptiveSession,
    loadingAdaptiveQuestion,
  } = useStore();

  if (!evaluation && !learningPlan) return null;

  return (
    <div className="max-w-4xl mx-auto py-8 animate-fade-in space-y-12">
      
      {/* HEADER SECTION */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center p-3 bg-indigo-900/40 rounded-full mb-2">
          <Brain className="w-8 h-8 text-indigo-400" />
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
          Your Intelligent Analysis
        </h2>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          We've analyzed your responses. Here is your current knowledge breakdown and your personalized roadmap to mastery.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          <Badge variant={aiSource === "fallback" ? "warning" : "success"} className="px-3 py-1">
            Analysis Source: {aiSource || "live"}
          </Badge>
          <Badge variant={questionSource === "fallback" ? "warning" : "primary"} className="px-3 py-1">
            Question Source: {questionSource || "live"}
          </Badge>
          <Badge variant={(stageSources?.evaluation || "live") === "fallback" ? "warning" : "default"} className="px-3 py-1">
            Evaluation: {stageSources?.evaluation || "live"}
          </Badge>
          <Badge variant={(stageSources?.learning_plan || "live") === "fallback" ? "warning" : "default"} className="px-3 py-1">
            Plan: {stageSources?.learning_plan || "live"}
          </Badge>
        </div>
        {resumeMessage ? (
          <p className="inline-flex items-center rounded-full border border-amber-200 bg-amber-900/40 px-4 py-2 text-sm text-amber-200">
            {resumeMessage}
          </p>
        ) : null}
        {aiSource === "fallback" ? (
          <div className="mx-auto max-w-2xl rounded-xl border border-amber-200 bg-amber-900/40/80 p-4 text-left text-sm text-amber-100">
            <p className="font-semibold mb-1">Live AI was rate-limited, so fallback logic was used.</p>
            {stageReasons?.evaluation ? <p>Evaluation: {stageReasons.evaluation}</p> : null}
            {stageReasons?.learning_plan ? <p>Plan: {stageReasons.learning_plan}</p> : null}
          </div>
        ) : null}
      </div>

      {/* EVALUATION SECTION */}
      {evaluation && (
        <section className="space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-2xl font-bold flex items-center gap-2 text-slate-100">
              <Target className="w-6 h-6 text-indigo-500" /> Assessment Results
            </h3>
            <Badge variant="primary" className="text-sm px-3 py-1">Level: {evaluation.level}</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-indigo-100 bg-indigo-950/30/40">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-indigo-100 flex items-center gap-2 text-lg">
                  <Gauge className="w-5 h-5" /> Behavior & Confidence
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Behavior</span>
                  <Badge variant="outline" className="capitalize">{evaluation.behavior}</Badge>
                </div>
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-400">Evaluation Confidence</span>
                    <span className="font-semibold text-slate-200">{Math.round((evaluation.evaluation_confidence || 0) * 100)}%</span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-indigo-950/300"
                      style={{ width: `${Math.round((evaluation.evaluation_confidence || 0) * 100)}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-amber-100 bg-amber-900/40/40">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-amber-100 flex items-center gap-2 text-lg">
                  <ListChecks className="w-5 h-5" /> Focus Areas
                </CardTitle>
              </CardHeader>
              <CardContent>
                {evaluation.recommended_focus_areas?.length ? (
                  <ul className="space-y-2">
                    {evaluation.recommended_focus_areas.map((item, i) => (
                      <li key={i} className="text-sm text-amber-100 flex items-start">
                        <span className="font-bold mr-2 text-amber-600">&bull;</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-amber-200/80">No focus areas generated.</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <Card className="border-emerald-100 bg-emerald-900/40/30">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-emerald-200 flex items-center gap-2 text-lg">
                  <Zap className="w-5 h-5" /> Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                {evaluation.strengths?.length > 0 ? (
                  <ul className="space-y-2">
                    {evaluation.strengths.map((item, i) => (
                      <li key={i} className="flex items-start text-sm text-emerald-100">
                        <CheckCircle className="w-4 h-4 mr-2 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-emerald-700/70 italic">No specific strengths identified yet.</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-rose-100 bg-rose-900/40/30">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-rose-200 flex items-center gap-2 text-lg">
                  <AlertTriangle className="w-5 h-5" /> Areas to Improve
                </CardTitle>
              </CardHeader>
              <CardContent>
                {evaluation.weaknesses?.length > 0 ? (
                  <ul className="space-y-2">
                    {evaluation.weaknesses.map((item, i) => (
                      <li key={i} className="flex items-start text-sm text-rose-100">
                        <div className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-2.5 shrink-0 mt-1.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-rose-700/70 italic">No specific weaknesses identified.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {evaluation.misconceptions?.length > 0 && (
            <Card className="border-amber-100 bg-amber-900/40/30">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-amber-200 text-lg">Key Misconceptions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {evaluation.misconceptions.map((item, i) => (
                     <li key={i} className="flex items-start text-sm text-amber-100">
                       <span className="font-bold mr-2 text-amber-600">&bull;</span>
                       <span>{item}</span>
                     </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {evaluation.confidence_gaps?.length > 0 && (
            <Card className="border-slate-800 bg-slate-900/40/40">
              <CardHeader className="pb-2 border-none">
                <CardTitle className="text-slate-100 text-lg">Confidence Gaps</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {evaluation.confidence_gaps.map((item, i) => (
                    <li key={i} className="text-sm text-slate-200 flex items-start">
                      <span className="font-bold mr-2 text-slate-400">&bull;</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </section>
      )}

      {/* LEARNING PLAN SECTION */}
      {learningPlan && (
        <section className="space-y-6 pt-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-2xl font-bold flex items-center gap-2 text-slate-100">
              <Navigation className="w-6 h-6 text-indigo-500" /> Personalized Roadmap
            </h3>
          </div>

          <Card className="shadow-lg border-indigo-100 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-950/300"></div>
            <CardContent className="p-8">
               <div className="mb-8">
                 <h4 className="text-sm font-bold uppercase tracking-wider text-indigo-500 mb-2">Core Concept Analogy</h4>
                 <p className="text-lg text-slate-100 leading-relaxed font-medium bg-indigo-950/30 p-4 rounded-xl border border-indigo-100/50">
                    "{learningPlan.analogy}"
                 </p>
               </div>

               <div className="space-y-8">
                  <div>
                    <h4 className="flex items-center font-bold text-white text-lg mb-4">
                      <BookOpen className="w-5 h-5 mr-2 text-indigo-500" /> Learning Steps
                    </h4>
                    <div className="space-y-4">
                      {learningPlan.learning_steps?.map((step, i) => (
                        <div key={i} className="flex border border-slate-800 rounded-xl p-4 bg-slate-900/50 backdrop-blur-sm border-slate-800 shadow-lg shadow-black/40 border border-slate-800">
                          <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-indigo-900/40 text-indigo-300 font-bold text-sm mr-4">
                            {i + 1}
                          </div>
                          <p className="text-sm text-slate-200 leading-relaxed pt-1">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {learningPlan.practice_questions?.length > 0 && (
                    <div>
                      <h4 className="font-bold text-white text-lg mb-4">Practice Questions</h4>
                      <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {learningPlan.practice_questions.map((item, i) => (
                          <li key={i} className="bg-slate-900/40 border border-slate-800 p-4 rounded-xl text-sm text-slate-200 flex items-start">
                             <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mr-2.5 shrink-0 mt-1.5" />
                             <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
               </div>
            </CardContent>
          </Card>
        </section>
      )}

      {/* FOOTER ACTIONS */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-center pt-8 pb-10">
        <Button
          variant="primary"
          size="lg"
          onClick={() => startAdaptiveSession(topic)}
          className="w-full sm:w-auto"
          loading={loadingAdaptiveQuestion}
        >
          {loadingAdaptiveQuestion ? "Starting adaptive loop..." : "Continue With Adaptive Practice"}
        </Button>
        <Button variant="secondary" size="lg" onClick={() => setView("dashboard")} className="w-full sm:w-auto">
          View Learning History
        </Button>
        <Button variant="outline" size="lg" onClick={resetStore} className="w-full sm:w-auto">
          <RotateCcw className="w-5 h-5 mr-2" /> Start New Topic
        </Button>
      </div>

    </div>
  );
}