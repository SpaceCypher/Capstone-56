import useStore from "./store/useDiagnosticStore";  
import Layout from "./layouts/Layout";  
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import LandingPage from "./pages/LandingPage";  
import DiagnosticPage from "./pages/DiagnosticPage";  
import ResultPage from "./pages/ResultPage";  
import DashboardPage from "./pages/DashboardPage";
import AdaptiveLearningPage from "./pages/AdaptiveLearningPage";
  
export default function App() {  
  const { view, user, authMode } = useStore();  
  
  return (  
    <Layout>  
      {!user && authMode === "login" && <LoginPage />}
      {!user && authMode === "signup" && <SignupPage />}
      {user && view === "landing" && <LandingPage />}  
      {user && view === "diagnostic" && <DiagnosticPage />}  
      {user && view === "analysis" && <ResultPage />}  
      {user && view === "dashboard" && <DashboardPage />}  
      {user && view === "adaptive" && <AdaptiveLearningPage />}  
    </Layout>  
  );  
} 
