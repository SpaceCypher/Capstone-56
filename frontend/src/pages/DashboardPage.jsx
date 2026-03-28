import { useEffect, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ChevronLeft,
  Clock3,
  PlayCircle,
  RefreshCw,
  Trash2,
} from "lucide-react";
import useStore from "../store/useDiagnosticStore";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Forms";

const LEVEL_VARIANT = {
  beginner: "warning",
  intermediate: "primary",
  advanced: "success",
};

const STATE_COLORS = {
  struggling: "bg-rose-500",
  guessing: "bg-amber-500",
  mastery: "bg-emerald-500",
  improving: "bg-indigo-950/300",
  neutral: "bg-slate-900/400",
};

export default function DashboardPage() {
  const {
    user,
    dashboard,
    userTopics,
    loadingDashboard,
    loadingUserTopics,
    deletingTopic,
    dashboardError,
    topicsError,
    loadingGenerate,
    loadDashboard,
    loadUserTopics,
    continueTopic,
    deleteTopicHistory,
    setView,
  } = useStore();

  const userId = (user?.user_id || "").trim();

  useEffect(() => {
    if (!userId) {
      return;
    }
    loadDashboard(userId);
    loadUserTopics(userId);
  }, [loadDashboard, loadUserTopics, userId]);

  const stateEntries = useMemo(() => {
    const breakdown = dashboard?.state_breakdown || {};
    return Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
  }, [dashboard]);

  const totalStates = useMemo(
    () => stateEntries.reduce((sum, [, count]) => sum + Number(count || 0), 0),
    [stateEntries]
  );

  return (
    <div className="max-w-5xl mx-auto py-6 animate-fade-in space-y-8">
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={() => setView("landing")}
          className="flex items-center text-sm font-medium text-slate-400 hover:text-indigo-400 transition-colors"
        >
          <ChevronLeft className="w-4 h-4 mr-1" /> Back to Home
        </button>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              loadDashboard(userId);
              loadUserTopics(userId);
            }}
            loading={loadingDashboard || loadingUserTopics}
            disabled={!userId}
          >
            {!loadingDashboard && !loadingUserTopics && <RefreshCw className="w-4 h-4 mr-2" />}
            Refresh
          </Button>
          <Button type="button" variant="outline" onClick={() => setView("landing")}>
            Start New Topic
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold tracking-tight text-white">Learning History Dashboard</h2>
        <p className="text-slate-400">
          Resume instantly from saved topics for user <span className="font-semibold text-slate-200">{user?.name || "Unknown"}</span>
        </p>
      </div>

      {topicsError ? (
        <Card className="border-rose-200 bg-rose-50/60">
          <CardContent className="py-4 text-rose-700 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {topicsError}
          </CardContent>
        </Card>
      ) : null}

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white">Previously Learned Topics</h3>
          <Badge variant="outline">{userTopics.length} topics</Badge>
        </div>

        {loadingUserTopics ? (
          <Card>
            <CardContent className="py-6 text-sm text-slate-400">Loading topic history...</CardContent>
          </Card>
        ) : userTopics.length === 0 ? (
          <Card>
            <CardContent className="py-6 text-sm text-slate-400">
              No saved topic history yet. Complete one diagnostic to start building your profile.
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {userTopics.map((topicItem) => {
              const progressPct = Math.round((topicItem.progress || 0) * 100);
              const weaknesses = topicItem.weaknesses || [];
              const level = String(topicItem.level || "beginner").toLowerCase();
              return (
                <Card key={`${topicItem.topic}-${topicItem.last_updated}`} className="shadow-xl shadow-black/50 border border-slate-800">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-3">
                      <CardTitle className="text-lg text-white">{topicItem.topic}</CardTitle>
                      <Badge variant={LEVEL_VARIANT[level] || "default"} className="capitalize">
                        {topicItem.level}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                        <span>Progress</span>
                        <span>{progressPct}%</span>
                      </div>
                      <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full rounded-full bg-indigo-600" style={{ width: `${progressPct}%` }} />
                      </div>
                    </div>

                    <div className="flex items-start gap-2 text-xs text-slate-400">
                      <Clock3 className="w-4 h-4 mt-0.5" />
                      <span>Last updated: {new Date(topicItem.last_updated).toLocaleString()}</span>
                    </div>

                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">Weak areas</p>
                      {weaknesses.length ? (
                        <div className="flex flex-wrap gap-2">
                          {weaknesses.slice(0, 3).map((weak) => (
                            <Badge key={weak} variant="danger" className="text-[11px]">
                              {weak}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-slate-400">No major weaknesses recorded.</p>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button
                        type="button"
                        className="flex-1"
                        onClick={() => continueTopic(topicItem.topic)}
                        loading={loadingGenerate}
                        disabled={deletingTopic === topicItem.topic}
                      >
                        {!loadingGenerate && <PlayCircle className="w-4 h-4 mr-2" />}
                        Continue
                      </Button>
                      <Button
                        type="button"
                        variant="danger"
                        className="px-4"
                        onClick={() => {
                          const confirmed = window.confirm(
                            `Delete saved history for ${topicItem.topic}? This cannot be undone.`
                          );
                          if (confirmed) {
                            deleteTopicHistory(topicItem.topic);
                          }
                        }}
                        loading={deletingTopic === topicItem.topic}
                        disabled={loadingGenerate}
                      >
                        {deletingTopic !== topicItem.topic && <Trash2 className="w-4 h-4" />}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      <section className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white">Behavior Signals</h3>
          <Badge variant="outline">{dashboard?.total_interactions || 0} interactions</Badge>
        </div>

        {dashboardError ? (
          <Card className="border-rose-200 bg-rose-50/60">
            <CardContent className="py-4 text-rose-700 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              {dashboardError}
            </CardContent>
          </Card>
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-slate-400 font-semibold">Total Interactions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-black text-white">{dashboard?.total_interactions || 0}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-slate-400 font-semibold">Weak Concepts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-black text-white">{dashboard?.weak_concepts?.length || 0}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-slate-400 font-semibold">Tracked States</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-black text-white">{stateEntries.length}</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" /> State Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {stateEntries.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/40 p-6 text-slate-400 text-sm">
                No state data yet. Submit attempts in adaptive mode to populate this chart.
              </div>
            ) : (
              stateEntries.map(([state, count]) => {
                const percentage = totalStates > 0 ? Math.round((count / totalStates) * 100) : 0;
                const barColor = STATE_COLORS[state] || "bg-slate-900/400";
                return (
                  <div key={state} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize font-semibold text-slate-200">{state}</span>
                      <span className="text-slate-400">{count} ({percentage}%)</span>
                    </div>
                    <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                      <div className={`h-full rounded-full ${barColor}`} style={{ width: `${percentage}%` }} />
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" /> Weak Concept Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard?.weak_concepts?.length ? (
              <div className="flex flex-wrap gap-2">
                {dashboard.weak_concepts.map((concept) => (
                  <Badge key={concept} variant="warning" className="px-3 py-1 text-xs">
                    {concept}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No weak concepts flagged yet.</p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
