import UploadForm from "./UploadForm";
import "./styles.css";

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <img src="https://rabbitt.ai/rabbits/rabbit1.svg" alt="RabbittAi" className="brand-logo" />
        <p className="brand-name">RabbittAi</p>
        <h1>Sales Insight Automator</h1>
        <p className="subtitle">
          Upload your sales data — get an AI-powered executive summary delivered
          straight to your inbox.
        </p>
      </header>

      <main className="card">
        <UploadForm />
      </main>
    </div>
  );
}
