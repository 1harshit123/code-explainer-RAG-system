import React, { useState, useRef, useEffect } from 'react';

export default function Chatbox({ onBackToIndexer }) {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Semantic indexing complete. Ask me anything about your repository modules, functions, or control flows.' }
    ]);
    const [input, setInput] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);

    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleQuerySubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userPrompt = input.trim();
        setInput('');
        setIsStreaming(true);

        setMessages((prev) => [
            ...prev,
            { role: 'user', content: userPrompt },
            { role: 'assistant', content: '' }
        ]);

        try {
            const response = await fetch('http://localhost:8000/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userPrompt }),
            });

            if (!response.body) throw new Error("ReadableStream infrastructure error.");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let accumulatedTokens = "";
            let streamBuffer = ""; 

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                streamBuffer += decoder.decode(value, { stream: true });

                const lines = streamBuffer.split("\n\n");

                streamBuffer = lines.pop() || "";

                for (const line of lines) {
                    const cleanLine = line.trim();
                    if (cleanLine.startsWith("data: ")) {
                        const jsonPayload = cleanLine.replace("data: ", "").trim();

                        try {
                            const parsed = JSON.parse(jsonPayload);

                            if (parsed.token) {
                                accumulatedTokens += parsed.token;

                                setMessages((prev) => {
                                    const updated = [...prev];
                                    updated[updated.length - 1] = {
                                        role: 'assistant',
                                        content: accumulatedTokens,
                                    };
                                    return updated;
                                });
                            } else if (parsed.error) {
                                console.error("Backend exception pipeline intercept:", parsed.error);
                            }
                        } catch (jsonParseError) {
                            console.error("Failed parsing incoming frame chunk:", jsonPayload, jsonParseError);
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Streaming connection error:", error);
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: '⚠️ Server stream execution failed or timed out.' }
            ]);
        } finally {
            setIsStreaming(false);
        }
    };

    return (
        <div className="w-full max-w-4xl h-full flex flex-col bg-neutral-950/40 border border-neutral-800/40 rounded-xl backdrop-blur-sm overflow-hidden shadow-2xl shadow-black/40">

            {/* Interface Header Module */}
            <div className="px-6 py-4 border-b border-neutral-800/60 bg-neutral-900/20 flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-2.5">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    <h3 className="text-sm font-medium tracking-tight text-neutral-200">Repository Agent Runtime</h3>
                </div>
                {/* Fixed back action handler hook point */}
                <button
                    onClick={onBackToIndexer}
                    className="text-[11px] font-mono tracking-wider uppercase bg-neutral-900 text-neutral-400 hover:text-white border border-neutral-800 px-3 py-1.5 rounded-md active:scale-95 transition-all duration-150"
                >
                    &lt; Index New Repo
                </button>
            </div>

            {/* Dynamic Message Feed Display Layout */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-neutral-800">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex flex-col max-w-[85%] lg:max-w-[75%] rounded-xl px-4 py-3.5 border transition-all duration-200 ${msg.role === 'user'
                                ? 'bg-neutral-900 border-neutral-800/80 text-neutral-100 ml-auto shadow-md'
                                : 'bg-neutral-950 text-neutral-300 border-neutral-900 mr-auto'
                            }`}
                    >
                        <span className="text-[9px] font-mono tracking-widest text-neutral-500 uppercase mb-1.5 select-none">
                            {msg.role === 'user' ? 'Context Query' : 'System Agent'}
                        </span>
                        <p className="text-sm leading-relaxed font-sans font-light whitespace-pre-wrap">
                            {msg.content}
                            {/* Render active typing blinking cursor indicator box ONLY for current streaming response element blocks */}
                            {isStreaming && idx === messages.length - 1 && (
                                <span className="inline-block w-1.5 h-4 ml-0.5 bg-neutral-400 animate-pulse align-middle"></span>
                            )}
                        </p>
                    </div>
                ))}
                {/* Hidden anchor element to handle target positioning calculation metrics */}
                <div ref={messagesEndRef} />
            </div>

            {/* Persistent Input Bar Form Element Layout */}
            <div className="p-4 border-t border-neutral-800/60 bg-neutral-950/80 backdrop-blur-md shrink-0">
                <form onSubmit={handleQuerySubmit} className="relative max-w-3xl mx-auto group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-neutral-800 to-neutral-700 rounded-xl blur opacity-10 group-focus-within:opacity-40 transition duration-300"></div>

                    <div className="relative flex items-center bg-neutral-900 border border-neutral-800 rounded-xl p-1.5 shadow-inner">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={isStreaming}
                            placeholder={isStreaming ? "Awaiting model token sequence packet resolution..." : "Ask questions about structural logic, references, or code vectors..."}
                            className="w-full bg-transparent px-4 py-2.5 text-sm text-neutral-200 placeholder-neutral-500 focus:outline-none disabled:opacity-40"
                        />
                        <button
                            type="submit"
                            disabled={isStreaming || !input.trim()}
                            className="bg-white text-neutral-950 font-medium text-xs tracking-wide uppercase px-5 py-2.5 rounded-lg hover:bg-neutral-200 active:scale-95 transition-all duration-150 shrink-0 disabled:opacity-20 disabled:pointer-events-none"
                        >
                            {isStreaming ? (
                                <div className="h-3.5 w-3.5 border-2 border-neutral-950 border-t-transparent rounded-full animate-spin" />
                            ) : (
                                'Query'
                            )}
                        </button>
                    </div>
                </form>
            </div>

        </div>
    );
}