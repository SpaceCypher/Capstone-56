import { create } from "zustand";
import {
  analyzeDiagnosticResponses,
  deleteUserTopic as deleteUserTopicApi,
  fetchQuestion,
  fetchQuestionSet,
  fetchDashboard as fetchBehaviorDashboard,
  generateDiagnosticQuestions,
  getUserTopicDetails,
  getUserTopics,
  loginUser,
  signupUser,
  submitAttempt,
} from "../services/api";

const AUTH_STORAGE_KEY = "neurolearn-auth-user";
const ADAPTIVE_SET_SIZE = 3;

function loadPersistedUser() {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    if (!parsed.user_id || !parsed.email || !parsed.name) {
      return null;
    }
    return {
      user_id: String(parsed.user_id),
      name: String(parsed.name),
      email: String(parsed.email),
    };
  } catch {
    return null;
  }
}

function persistUser(user) {
  if (typeof window === "undefined") {
    return;
  }

  if (!user) {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
}

const initialUser = loadPersistedUser();

const useDiagnosticStore = create((set, get) => ({
  user: initialUser,
  authMode: "login", // login | signup
  authLoading: false,
  authError: null,
  topic: "",
  questions: [],
  answers: {},
  unknownAnswers: {},
  confidence: {},
  evaluation: null,
  learningPlan: null,
  aiSource: null,
  questionSource: null,
  stageSources: {},
  stageReasons: {},
  dashboard: null,
  userTopics: [],
  deletingTopic: "",
  resumeMessage: "",

  adaptiveQuestion: null,
  adaptiveQuestionSet: [],
  adaptiveQuestionIndex: 0,
  adaptiveFeedback: null,
  adaptiveSessionTopic: "",
  adaptiveSessionConcept: "loops",
  adaptiveAnswer: "",
  
  loadingGenerate: false,
  loadingAnalyze: false,
  loadingDashboard: false,
  loadingUserTopics: false,
  loadingAdaptiveQuestion: false,
  loadingAdaptiveSubmit: false,
  error: null,
  dashboardError: null,
  topicsError: null,
  adaptiveError: null,
  
  view: "landing", // landing | diagnostic | analysis | dashboard | adaptive

  getUserId: () => (get().user?.user_id || "").trim(),
  setAuthMode: (mode) => set({ authMode: mode, authError: null }),
  clearAuthError: () => set({ authError: null }),

  signup: async ({ name, email, password }) => {
    set({ authLoading: true, authError: null });
    try {
      const response = await signupUser({ name, email, password });
      const user = response?.user || null;
      if (!user?.user_id) {
        throw new Error("Signup succeeded but user data was not returned.");
      }

      persistUser(user);
      set({
        user,
        authLoading: false,
        authError: null,
      });
      get().resetStore();
    } catch (err) {
      set({ authLoading: false, authError: err.message || "Signup failed." });
    }
  },

  login: async ({ email, password }) => {
    set({ authLoading: true, authError: null });
    try {
      const response = await loginUser({ email, password });
      const user = response?.user || null;
      if (!user?.user_id) {
        throw new Error("Login succeeded but user data was not returned.");
      }

      persistUser(user);
      set({
        user,
        authLoading: false,
        authError: null,
      });
      get().resetStore();
    } catch (err) {
      set({ authLoading: false, authError: err.message || "Login failed." });
    }
  },

  logout: () => {
    persistUser(null);
    set({
      user: null,
      authMode: "login",
      authLoading: false,
      authError: null,
      topic: "",
      questions: [],
      answers: {},
      unknownAnswers: {},
      confidence: {},
      evaluation: null,
      learningPlan: null,
      aiSource: null,
      questionSource: null,
      stageSources: {},
      stageReasons: {},
      dashboard: null,
      userTopics: [],
      deletingTopic: "",
      resumeMessage: "",
      adaptiveQuestion: null,
      adaptiveQuestionSet: [],
      adaptiveQuestionIndex: 0,
      adaptiveFeedback: null,
      adaptiveSessionTopic: "",
      adaptiveSessionConcept: "loops",
      adaptiveAnswer: "",
      loadingGenerate: false,
      loadingAnalyze: false,
      loadingDashboard: false,
      loadingUserTopics: false,
      loadingAdaptiveQuestion: false,
      loadingAdaptiveSubmit: false,
      error: null,
      dashboardError: null,
      topicsError: null,
      adaptiveError: null,
      view: "landing",
    });
  },

  setTopic: (topic) => set({ topic }),
  setAnswer: (id, val) =>
    set((state) => ({
      answers: { ...state.answers, [id]: val },
      unknownAnswers: { ...state.unknownAnswers, [id]: false },
    })),
  setUnknownAnswer: (id, value) =>
    set((state) => ({
      unknownAnswers: { ...state.unknownAnswers, [id]: Boolean(value) },
    })),
  setConfidence: (id, val) => set((state) => ({ confidence: { ...state.confidence, [id]: val } })),
  setAdaptiveAnswer: (value) => set({ adaptiveAnswer: value }),
  
  setView: (view) => set({ view }),
  setError: (error) => set({ error }),

  loadUserTopics: async (userIdArg) => {
    const selectedUser = (userIdArg || get().getUserId()).trim();
    if (!selectedUser) {
      set({
        userTopics: [],
        loadingUserTopics: false,
        topicsError: "Please log in to load topic history.",
      });
      return;
    }

    set({ loadingUserTopics: true, topicsError: null });
    try {
      const response = await getUserTopics(selectedUser);
      set({ userTopics: response.topics || [] });
    } catch (err) {
      set({ topicsError: err.message || "Failed to load topic history." });
    } finally {
      set({ loadingUserTopics: false });
    }
  },

  deleteTopicHistory: async (topicArg) => {
    const state = get();
    const selectedTopic = (topicArg || "").trim();
    if (!selectedTopic) {
      return;
    }

    const userId = state.getUserId();
    if (!userId) {
      set({ topicsError: "Please log in to manage topic history." });
      return;
    }

    set({ deletingTopic: selectedTopic, topicsError: null });
    try {
      await deleteUserTopicApi(userId, selectedTopic);
      set((prev) => ({
        userTopics: (prev.userTopics || []).filter((item) => item.topic !== selectedTopic),
      }));
      await get().loadDashboard(userId);
    } catch (err) {
      set({ topicsError: err.message || "Failed to delete topic history." });
    } finally {
      set({ deletingTopic: "" });
    }
  },

  continueTopic: async (topicArg) => {
    const state = get();
    const selectedTopic = (topicArg || state.topic || "").trim();
    if (!selectedTopic) {
      set({ error: "Topic is required to continue." });
      return;
    }
    const userId = state.getUserId();
    if (!userId) {
      set({ error: "Please log in to continue a saved topic." });
      return;
    }

    set({ loadingGenerate: true, error: null });
    try {
      const details = await getUserTopicDetails(userId, selectedTopic);
      set({
        topic: details.topic,
        evaluation: {
          level: details.level,
          behavior: "inconsistent",
          strengths: details.strengths || [],
          weaknesses: details.weaknesses || [],
          misconceptions: details.misconceptions || [],
          confidence_gaps: [],
          recommended_focus_areas: details.weaknesses || [],
          evaluation_confidence: details.progress || 0.6,
        },
        learningPlan: details.learning_plan || null,
        aiSource: "history",
        questionSource: "history",
        stageSources: {},
        stageReasons: {},
        resumeMessage: details.resume_message || "Resumed from your saved history.",
        view: "analysis",
      });
    } catch (err) {
      set({ error: err.message || "Failed to continue this topic." });
    } finally {
      set({ loadingGenerate: false });
    }
  },

  loadAdaptiveQuestion: async (conceptIdArg, topicArg, seedQuestionArg = null) => {
    const state = get();
    const conceptId = (conceptIdArg || state.adaptiveSessionConcept || "general").trim() || "general";
    const topic = (topicArg || state.adaptiveSessionTopic || state.topic || conceptId || "General").trim() || "General";
    const seedQuestion = seedQuestionArg && typeof seedQuestionArg === "object" ? seedQuestionArg : null;

    set({ loadingAdaptiveQuestion: true, adaptiveError: null });
    try {
      const response = await fetchQuestionSet(conceptId, topic, ADAPTIVE_SET_SIZE);
      const generatedSet = Array.isArray(response?.questions) ? response.questions : [];

      const merged = seedQuestion ? [seedQuestion, ...generatedSet] : generatedSet;
      const deduped = [];
      const seen = new Set();
      for (const item of merged) {
        if (!item || typeof item !== "object") {
          continue;
        }
        const prompt = String(item.prompt || "").trim().toLowerCase().replace(/\s+/g, " ");
        const key = prompt;
        if (!prompt || seen.has(key)) {
          continue;
        }
        seen.add(key);
        deduped.push(item);
        if (deduped.length >= ADAPTIVE_SET_SIZE) {
          break;
        }
      }

      let retryCount = 0;
      const maxRetries = 6;
      while (deduped.length < ADAPTIVE_SET_SIZE && retryCount < maxRetries) {
        retryCount += 1;
        const extra = await fetchQuestion(conceptId, topic);
        const prompt = String(extra?.prompt || "").trim().toLowerCase().replace(/\s+/g, " ");
        const key = prompt;
        if (!prompt || seen.has(key)) {
          continue;
        }
        seen.add(key);
        deduped.push(extra);
      }

      while (deduped.length < ADAPTIVE_SET_SIZE && deduped.length > 0) {
        deduped.push({ ...deduped[deduped.length - 1] });
      }

      const firstQuestion = deduped[0] || seedQuestion;
      if (!firstQuestion) {
        throw new Error("No adaptive question returned.");
      }

      set({
        adaptiveQuestionSet: deduped,
        adaptiveQuestionIndex: 0,
        adaptiveQuestion: firstQuestion,
        adaptiveSessionConcept: firstQuestion?.concept_id || conceptId,
        adaptiveSessionTopic: firstQuestion?.topic || topic,
        adaptiveAnswer: "",
      });
    } catch (err) {
      if (seedQuestion) {
        set({
          adaptiveQuestionSet: [seedQuestion],
          adaptiveQuestionIndex: 0,
          adaptiveQuestion: seedQuestion,
          adaptiveSessionConcept: seedQuestion?.concept_id || conceptId,
          adaptiveSessionTopic: seedQuestion?.topic || topic,
          adaptiveAnswer: "",
          adaptiveError: null,
        });
      } else {
        set({ adaptiveError: err.message || "Failed to fetch adaptive question set." });
      }
    } finally {
      set({ loadingAdaptiveQuestion: false });
    }
  },

  cycleAdaptiveQuestion: async () => {
    const state = get();
    const setList = Array.isArray(state.adaptiveQuestionSet) ? state.adaptiveQuestionSet : [];

    if (setList.length === 0) {
      await get().loadAdaptiveQuestion(state.adaptiveSessionConcept, state.adaptiveSessionTopic);
      return;
    }

    const nextIndex = (state.adaptiveQuestionIndex + 1) % setList.length;
    const nextQuestion = setList[nextIndex];
    set({
      adaptiveQuestionIndex: nextIndex,
      adaptiveQuestion: nextQuestion,
      adaptiveSessionConcept: nextQuestion?.concept_id || state.adaptiveSessionConcept,
      adaptiveSessionTopic: nextQuestion?.topic || state.adaptiveSessionTopic,
      adaptiveAnswer: "",
      adaptiveError: null,
    });
  },

  startAdaptiveSession: async (topicArg) => {
    const state = get();
    let selectedTopic = (topicArg || state.topic || "").trim();

    if (!selectedTopic) {
      const existingTopics = state.userTopics || [];
      if (existingTopics.length === 0) {
        await state.loadUserTopics(state.getUserId());
      }
      const refreshedTopics = get().userTopics || [];
      selectedTopic = (refreshedTopics[0]?.topic || "").trim();
    }

    if (!selectedTopic) {
      set({ adaptiveError: "No learned topic found. Complete a diagnostic first." });
      return;
    }

    const concept = selectedTopic
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-") || "general";

    set({
      view: "adaptive",
      topic: selectedTopic,
      adaptiveSessionTopic: selectedTopic,
      adaptiveSessionConcept: concept,
      adaptiveFeedback: null,
      adaptiveQuestion: null,
      adaptiveQuestionSet: [],
      adaptiveQuestionIndex: 0,
      adaptiveAnswer: "",
      adaptiveError: null,
    });

    await get().loadAdaptiveQuestion(concept, selectedTopic);
  },

  handleAdaptiveSubmit: async () => {
    const state = get();
    const question = state.adaptiveQuestion;
    if (!question) {
      set({ adaptiveError: "No question loaded yet. Please refresh question." });
      return;
    }

    const answer = (state.adaptiveAnswer || "").trim();
    if (!answer) {
      set({ adaptiveError: "Please enter your answer before submitting." });
      return;
    }

    set({ loadingAdaptiveSubmit: true, adaptiveError: null });
    try {
      const userId = state.getUserId();
      if (!userId) {
        throw new Error("Please log in to submit adaptive answers.");
      }

      const payload = {
        user_id: userId,
        concept_id: question.concept_id || state.adaptiveSessionConcept || "loops",
        question_id: question.question_id,
        topic: question.topic || state.adaptiveSessionTopic || state.topic || "General",
        question_prompt: question.prompt || "",
        expected_answer: question.expected_answer || "",
        answer,
      };

      const response = await submitAttempt(payload);
      const nextQuestion = response.next_question || null;

      set({
        adaptiveFeedback: response.adaptive || null,
        adaptiveSessionTopic: nextQuestion?.topic || state.adaptiveSessionTopic,
        adaptiveSessionConcept: nextQuestion?.concept_id || state.adaptiveSessionConcept,
      });

      await get().loadAdaptiveQuestion(
        nextQuestion?.concept_id || state.adaptiveSessionConcept,
        nextQuestion?.topic || state.adaptiveSessionTopic || state.topic || "General",
        nextQuestion,
      );

      await get().loadDashboard(payload.user_id);
    } catch (err) {
      set({ adaptiveError: err.message || "Failed to submit adaptive attempt." });
    } finally {
      set({ loadingAdaptiveSubmit: false });
    }
  },

  loadDashboard: async (userIdArg) => {
    const selectedUser = (userIdArg || get().getUserId()).trim();
    if (!selectedUser) {
      set({
        dashboard: null,
        loadingDashboard: false,
        dashboardError: "Please log in to load your dashboard.",
      });
      return;
    }

    set({ loadingDashboard: true, dashboardError: null });
    try {
      const dashboard = await fetchBehaviorDashboard(selectedUser);
      set({ dashboard });
    } catch (err) {
      set({ dashboardError: err.message || "Failed to load behavior dashboard." });
    } finally {
      set({ loadingDashboard: false });
    }
  },

  canAnalyze: () => {
    const { questions, answers, unknownAnswers, confidence } = get();
    if (questions.length === 0) return false;
    return questions.every((q) => {
      const ans = (answers[q.id] || "").trim();
      const doesntKnow = Boolean(unknownAnswers[q.id]);
      const conf = confidence[q.id];
      return (Boolean(ans) || doesntKnow) && Boolean(conf);
    });
  },

  handleGenerate: async () => {
    const { topic } = get();
    const userId = get().getUserId();
    const trimmedTopic = topic.trim();
    if (!userId) {
      set({ error: "Please log in to start your diagnostic." });
      return;
    }
    if (!trimmedTopic) {
      set({ error: "Please enter a topic." });
      return;
    }

    set({
      error: null,
      evaluation: null,
      learningPlan: null,
      aiSource: null,
      questionSource: null,
      stageSources: {},
      stageReasons: {},
      resumeMessage: "",
      loadingGenerate: true,
    });

    try {
      try {
        const details = await getUserTopicDetails(userId, trimmedTopic);
        set({
          topic: details.topic,
          evaluation: {
            level: details.level,
            behavior: "inconsistent",
            strengths: details.strengths || [],
            weaknesses: details.weaknesses || [],
            misconceptions: details.misconceptions || [],
            confidence_gaps: [],
            recommended_focus_areas: details.weaknesses || [],
            evaluation_confidence: details.progress || 0.6,
          },
          learningPlan: details.learning_plan || null,
          aiSource: "history",
          questionSource: "history",
          stageSources: {},
          stageReasons: {},
          resumeMessage: details.resume_message || "Resumed from your saved history.",
          view: "analysis",
        });
        return;
      } catch (historyErr) {
        if (historyErr && historyErr.status !== 404) {
          throw historyErr;
        }
      }

      const response = await generateDiagnosticQuestions(trimmedTopic, userId);
      const questionsData = response.questions || [];
      
      const nextConfidence = {};
      const nextAnswers = {};
      const nextUnknownAnswers = {};
      for (const q of questionsData) {
        nextConfidence[q.id] = "medium";
        nextAnswers[q.id] = "";
        nextUnknownAnswers[q.id] = false;
      }

      set({ 
        questions: questionsData, 
        confidence: nextConfidence, 
        answers: nextAnswers,
        unknownAnswers: nextUnknownAnswers,
        questionSource: response.ai_source || "live",
        resumeMessage: "",
        view: "diagnostic"
      });
    } catch (err) {
      set({ error: err.message || "Failed to generate diagnostic questions." });
    } finally {
      set({ loadingGenerate: false });
    }
  },

  handleAnalyze: async () => {
    const state = get();
    const userId = state.getUserId();
    if (!userId) {
      set({ error: "Please log in to analyze responses." });
      return;
    }
    if (!state.canAnalyze()) {
      set({ error: "Please provide answer and confidence for all questions." });
      return;
    }

    set({ error: null, loadingAnalyze: true });

    try {
      const payload = state.questions.map((q) => ({
        question_id: q.id,
        question: q.question,
        answer: state.unknownAnswers[q.id] ? "" : state.answers[q.id].trim(),
        doesnt_know: Boolean(state.unknownAnswers[q.id]),
        confidence: state.confidence[q.id],
      }));

      const response = await analyzeDiagnosticResponses(
        state.topic.trim(),
        payload,
        userId
      );

      set({
        evaluation: response.evaluation || null,
        learningPlan: response.learning_plan || null,
        aiSource: response.ai_source || "live",
        stageSources: response.stage_sources || {},
        stageReasons: response.stage_reasons || {},
        resumeMessage: "",
        view: "analysis"
      });

      await get().loadDashboard(userId);
      await get().loadUserTopics(userId);
    } catch (err) {
      set({ error: err.message || "Failed to analyze responses." });
    } finally {
      set({ loadingAnalyze: false });
    }
  },

  resetStore: () => {
    set({
      topic: "",
      questions: [],
      answers: {},
      unknownAnswers: {},
      confidence: {},
      evaluation: null,
      learningPlan: null,
      aiSource: null,
      questionSource: null,
      stageSources: {},
      stageReasons: {},
      dashboard: null,
      userTopics: [],
      deletingTopic: "",
      loadingDashboard: false,
      loadingUserTopics: false,
      topicsError: null,
      resumeMessage: "",
      error: null,
      dashboardError: null,
      adaptiveQuestion: null,
      adaptiveQuestionSet: [],
      adaptiveQuestionIndex: 0,
      adaptiveFeedback: null,
      adaptiveSessionTopic: "",
      adaptiveSessionConcept: "loops",
      adaptiveAnswer: "",
      adaptiveError: null,
      view: "landing"
    });
  }
}));

export default useDiagnosticStore;