import { ChevronLeft, CheckCircle2, HelpCircle } from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Label, Textarea, Badge } from "../components/ui/Forms";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";

export default function DiagnosticPage() {
  const { 
    topic, 
    questions, 
    answers, 
    unknownAnswers,
    confidence,
    setAnswer, 
    setUnknownAnswer,
    setConfidence,
    handleAnalyze, 
    loadingAnalyze, 
    canAnalyze,
    setView,
    error
  } = useStore();

  const answeredCount = questions.filter(
    (q) => (answers[q.id] || "").trim() || unknownAnswers[q.id]
  ).length;
  const progressPercent = Math.round((answeredCount / questions.length) * 100);

  return (
    <div className="max-w-3xl mx-auto py-6 animate-fade-in">
      <div className="mb-8">
        <button 
          onClick={() => setView('landing')}
          className="flex items-center text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors mb-4"
        >
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Setup
        </button>
        <div className="flex items-end justify-between mb-4">
          <div>
            <h2 className="text-3xl font-extrabold tracking-tight text-white">Diagnostic Assessment</h2>
            <p className="text-slate-400 mt-1">Topic: <span className="font-semibold text-slate-200">{topic}</span></p>
          </div>
          <Badge variant="primary" className="text-sm px-3 py-1">
            {answeredCount} / {questions.length} Answered
          </Badge>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
          <div 
            className="bg-indigo-500 h-2.5 rounded-full transition-all duration-500 ease-in-out" 
            style={{ width: `${progressPercent}%` }}
          ></div>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 text-red-400 p-4 rounded-xl mb-6 font-medium border border-red-800 flex items-center">
          {error}
        </div>
      )}

      <div className="space-y-8">
        {questions.map((question, index) => (
          <Card key={question.id} className="relative overflow-visible shadow-xl shadow-black/50 border border-slate-800 hover:shadow-lg transition-shadow">
            <div className="absolute -left-3 -top-3 w-8 h-8 bg-indigo-500 text-white rounded-full flex items-center justify-center font-bold text-sm shadow-xl shadow-black/50 border border-slate-800">
              {index + 1}
            </div>
            
            <CardHeader className="pb-4 pt-6">
              <div className="flex justify-between items-start mb-2">
                <Badge variant="outline" className="uppercase text-[10px] tracking-wider font-bold">
                  {question.type}
                </Badge>
              </div>
              <CardTitle className="text-lg leading-relaxed">{question.question}</CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor={`answer-${question.id}`}>Your Answer</Label>
                <div className="mt-2 mb-3">
                  <button
                    type="button"
                    onClick={() => setUnknownAnswer(question.id, !unknownAnswers[question.id])}
                    className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors
                      ${unknownAnswers[question.id]
                        ? "border-amber-700 bg-amber-900/50 text-amber-400"
                        : "border-slate-800 bg-slate-900/50 backdrop-blur-sm border-slate-800 text-slate-300 hover:bg-slate-900/40"
                      }
                    `}
                  >
                    {unknownAnswers[question.id] ? "Marked as: I don't know" : "I don't know this answer"}
                  </button>
                </div>
                <Textarea
                  id={`answer-${question.id}`}
                  placeholder={
                    unknownAnswers[question.id]
                      ? "You marked this as 'I don't know'. Toggle off to type an answer."
                      : "Type your answer here... Be as descriptive as possible."
                  }
                  className="mt-2"
                  value={answers[question.id] || ""}
                  onChange={(e) => setAnswer(question.id, e.target.value)}
                  disabled={Boolean(unknownAnswers[question.id])}
                />
              </div>

              <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                <div>
                  <Label htmlFor={`conf-${question.id}`} className="flex items-center gap-2 mb-2">
                    <HelpCircle className="w-4 h-4 text-slate-400" /> Confidence Level
                  </Label>
                  <div className="flex gap-2">
                    {['low', 'medium', 'high'].map(level => (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setConfidence(question.id, level)}
                        className={`flex-1 py-3 px-2 rounded-xl text-sm font-medium capitalize transition-all border
                          ${confidence[question.id] === level 
                            ? 'bg-indigo-500 text-white shadow-xl shadow-black/50 border border-slate-800 border-indigo-600' 
                            : 'bg-slate-900/50 backdrop-blur-sm border-slate-800 text-slate-300 border-slate-800 hover:bg-slate-900/40 hover:border-slate-700'
                          }
                        `}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-10 mb-20 sticky bottom-6 z-40 bg-slate-900/50 backdrop-blur-sm border-slate-800/80 backdrop-blur-md p-4 rounded-2xl border border-slate-800/60 shadow-xl flex items-center justify-between">
        <p className="text-sm font-medium text-slate-300 hidden sm:block">
          Complete all fields before analyzing.
        </p>
        <Button 
          onClick={handleAnalyze} 
          disabled={loadingAnalyze || !canAnalyze()}
          loading={loadingAnalyze}
          size="lg"
          className="w-full sm:w-auto"
        >
          {!loadingAnalyze && (
            <>
              Analyze Responses <CheckCircle2 className="w-5 h-5 ml-2" />
            </>
          )}
          {loadingAnalyze && "AI is Analyzing..."}
        </Button>
      </div>
    </div>
  );
}