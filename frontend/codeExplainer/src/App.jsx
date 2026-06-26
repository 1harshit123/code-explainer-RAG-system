import { useEffect, useState } from 'react'
import Chatbox from './component/Chatbox';
import axios from "axios";  
import AuthPage from './component/AuthPage'; 

import './App.css'

axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');

    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

function App() {
  const [viewState, setViewState] = useState('idle')
  const [repoLink, setRepoLink] = useState('');
  const [streamingText, setStreamingText] = useState("");
  const [statusMessage, setStatusMessage] = useState('System ready. Awaiting repository initialization...');
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionID, setSessionID] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuthPage, setShowAuthPage] = useState(false);


  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setIsAuthenticated(false);
        return;
      }

      try {
        await axios.get("http://localhost:8000/api/auth/getuser", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem("token");
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setViewState('idle');
    setSessionID(null);
  };
  const handleBackToIndexer = () => {
    try {
      if(sessionID){
        axios.delete(`http://localhost:8000/api/chat/history/${sessionID}`)
      }
      
    } catch (error) {
      console.log("Failed to delete the session", error);
    }

    setSessionID(null);
    setRepoLink("");
    setViewState("idle");
    setStatusMessage(
      "System ready. Awaiting repository initialization..."
    );
  }


  const handleInsert = async (e) => {

    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }
    e.preventDefault();
    if (!repoLink.trim()) return;

    const githubRegex = /^(https:\/\/github\.com\/|git@github\.com:)[a-zA-Z0-9-_.]+\/[a-zA-Z0-9-_.]+$/;

    if (!githubRegex.test(repoLink.trim())) {
      alert("Please enter a valid GitHub repository URL");
      return;
    }

    setViewState('loading')
    setIsProcessing(true);

      axios.post("http://localhost:8000/api/repo", { repoLink: repoLink })
        .then((repoResponse) => {
          console.log("Repo Ingestion Response:", repoResponse);
          if (repoResponse.data && repoResponse.data.Status === "Success") {
            return axios.post("http://localhost:8000/api/chat/session", { repoLink: repoLink });
          } else {
            throw new Error("Error in getting success response from ingestion backend");
          }
        })
        .then((sessionResponse) => {
          console.log("Session Creation Response:", sessionResponse);
          console.log("Session response data", sessionResponse.data)
          console.log("Session response data", sessionResponse.data.session_id)

          if (sessionResponse && sessionResponse.data && sessionResponse.data.session_id) {
            setSessionID(sessionResponse.data.session_id);
            setStatusMessage(`Active Session Mountpoint: ID ${sessionResponse.data.session_id}`);
            setViewState('chat');
          } else {
            throw new Error("Failed to register session space within PostgreSQL context.");
          }
        })
        .catch((error) => {
          console.error("Connection flow failed:", error);
          setStatusMessage("System core failure. Check terminal traceback.");
          setViewState('idle');
        })
        .finally(() => {
          setIsProcessing(false);
        });
    
   
  };


  return (
    <>
      <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans antialiased selection:bg-neutral-800 selection:text-white">

        <header className="border-b border-neutral-800/60 bg-neutral-900/40 backdrop-blur-md px-6 py-3 flex items-center justify-between sticky top-0 z-50">
          <div className="flex items-center space-x-3">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-mono tracking-wider uppercase text-neutral-400">codeRAG Core Engine v1.0</span>
          </div>
          <div className="text-xs font-mono text-neutral-400 max-w-md">
            <span className="text-neutral-500">Status:</span> {statusMessage}
          </div>
          {!isAuthenticated ? (
            <button
              onClick={() => setShowAuthPage(true)}
              className="text-xs font-bold tracking-wide uppercase bg-emerald-500 text-neutral-950 px-5 py-2 rounded-md hover:bg-emerald-400 active:scale-95 transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            >
              Sign In / Register
            </button>
          ) : (
            <button
              onClick={handleLogout}
              className="text-xs font-medium tracking-wide uppercase text-neutral-400 hover:text-white transition-colors"
            >
              Logout
            </button>
          )}
        </header>

        <main className="flex-1 grid grid-cols-12 overflow-hidden h-[calc(100vh-45px)]">
          <section className="col-span-3 border-r border-neutral-800/40 bg-neutral-950 p-6 flex flex-col justify-between hidden lg:flex">
            <div className="space-y-6">
              <div>
                <h1 className="text-lg font-semibold tracking-tight text-white">Repository Indexer</h1>
                <p className="text-xs text-neutral-400 mt-1">Abstract structural components and create semantic embeddings instantly.</p>
              </div>

              <div className="border border-neutral-800/80 rounded-lg p-4 bg-neutral-900/20 space-y-3">
                <span className="text-xs font-mono uppercase text-neutral-500 tracking-wider block">Local State Specs</span>
                <div className="flex justify-between text-xs"><span className="text-neutral-400">Database Context</span><span className="font-mono text-neutral-300">ChromaDB (HNSW)</span></div>
                <div className="flex justify-between text-xs"><span className="text-neutral-400">Distance Space</span><span className="font-mono text-neutral-300">Cosine Closeness</span></div>
                <div className="flex justify-between text-xs"><span className="text-neutral-400">Active Framework</span><span className="font-mono text-neutral-300">LangGraph Agent Loop</span></div>
              </div>
            </div>

            <div className="text-[10px] font-mono text-neutral-600 border-t border-neutral-900 pt-4">
              Authorized session instance via system memory layers.
            </div>
          </section>

          {/* Central Workspace Canvas Area */}
          <section className="col-span-12 lg:col-span-9 bg-neutral-900/20 flex flex-col items-center justify-center p-6 relative">

            {/* Background decorative glowing matrix grid */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f1f1f_1px,transparent_1px),linear-gradient(to_bottom,#1f1f1f_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />

            {/* Central Target Input Group */}
            <div className="w-full max-w-2xl space-y-6 relative z-10 px-4">
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">Analyze Code Architecture</h2>
                <p className="text-sm text-neutral-400 max-w-md mx-auto">
                  Paste a Git URL or absolute local file directory path below to mount your semantic RAG agent network.
                </p>
              </div>

              {viewState == 'idle' && (<><form onSubmit={handleInsert} className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-neutral-800 to-neutral-700 rounded-xl blur opacity-30 group-focus-within:opacity-60 transition duration-300" />
                <div className="relative flex items-center bg-neutral-900 border border-neutral-800 rounded-xl p-2 shadow-2xl shadow-black/80">
                  <input
                    type="text"
                    value={repoLink}
                    onChange={(e) => setRepoLink(e.target.value)}
                    disabled={isProcessing}
                    placeholder="https://github.com/username/repository-name.git"
                    className="w-full bg-transparent px-4 py-3 text-sm text-neutral-200 placeholder-neutral-500 focus:outline-none disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={isProcessing || !repoLink.trim()}
                    className="bg-white text-neutral-950 font-medium text-xs tracking-wide uppercase px-6 py-3.5 rounded-lg hover:bg-neutral-200 active:scale-95 disabled:opacity-30 disabled:pointer-events-none transition-all duration-150 flex items-center shrink-0"
                  >
                    {isProcessing ? (
                      <div className="h-4 w-4 border-2 border-neutral-950 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      'Insert'
                    )}
                  </button>
                </div>
              </form>

              {/* Quick-select structural recommendations anchor helper */}
              <div className="flex items-center justify-center space-x-2 text-xs text-neutral-500">
                <span>Supports AST structure definitions for:</span>
                <span className="font-mono text-neutral-400 bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 rounded">Python</span>
                <span className="font-mono text-neutral-400 bg-neutral-900 border border-neutral-800 px-1.5 py-0.5 rounded">TypeScript</span>
              </div>
            </>)}
            {viewState === "chat" &&(
                <Chatbox key={sessionID} sessionId={sessionID} onBackToIndexer={handleBackToIndexer}/>
            )}
            {viewState === "loading" &&(
              <>
                  <div className="flex flex-col items-center justify-center space-y-6 py-12 relative z-10 animate-fade-in">
                    <div className="relative flex items-center justify-center">
                      <div className="absolute h-16 w-16 rounded-full border border-emerald-500/30 animate-ping duration-1000" />
                      <div className="h-14 w-14 rounded-full border-2 border-neutral-800 border-t-emerald-500 animate-spin [animation-duration:0.8s]" />
                      <div className="absolute h-3 w-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                    </div>
                    <div className="text-center space-y-1.5">
                      <h3 className="text-xs font-mono tracking-widest text-emerald-400 uppercase font-medium">
                        Assembling Semantic Index
                      </h3>
                      <p className="text-xs text-neutral-500 font-mono animate-pulse max-w-xs mx-auto">
                        Cloning repository architecture, parsing AST nodes, and mapping vectors...
                      </p>
                    </div>
                  </div>
              </>
            )}


              <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${showAuthPage ? 'pointer-events-auto' : 'pointer-events-none'
                }`}>

                <div
                  className={`absolute inset-0 transition-all duration-300 ease-out ${showAuthPage
                      ? 'bg-black/40 backdrop-blur-md'
                      : 'bg-black/0 backdrop-blur-none'
                    }`}
                  onClick={() => setShowAuthPage(false)}
                />

                <div
                  className={`relative z-10 w-full max-w-sm transition-all duration-300 ease-out transform ${showAuthPage
                      ? 'scale-100 translate-y-0 opacity-100'
                      : 'scale-95 translate-y-4 opacity-0'
                    }`}
                >
                  <AuthPage
                    onLoginSuccess={() => {
                      setIsAuthenticated(true);
                      setShowAuthPage(false);
                    }}
                    onClose={() => setShowAuthPage(false)}
                  />
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </>
  )
}

export default App
