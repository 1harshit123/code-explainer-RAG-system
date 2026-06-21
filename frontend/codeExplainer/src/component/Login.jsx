import { useState } from 'react';

// Reusable glowing input component matching your App.jsx aesthetic
const InputField = ({ type, placeholder, value, onChange }) => (
    <div className="relative group w-full">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-neutral-800 to-neutral-700 rounded-xl blur opacity-30 group-focus-within:opacity-60 transition duration-300" />
        <div className="relative flex items-center bg-neutral-900 border border-neutral-800 rounded-xl shadow-2xl shadow-black/80">
            <input
                type={type}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                className="w-full bg-transparent px-4 py-3 text-sm text-neutral-200 placeholder-neutral-500 focus:outline-none"
            />
        </div>
    </div>
);

export default function AuthPage({ onLoginSuccess }) {
    const [isLogin, setIsLogin] = useState(true);

    const [emailOrUsername, setEmailOrUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [email, setEmail] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (isLogin) {
            console.log("Logging in with:", { emailOrUsername, password });
        } else {
            console.log("Signing up with:", { username: emailOrUsername, email, password, confirmPassword });
        }
    };

    return (
        <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans antialiased selection:bg-neutral-800 selection:text-white items-center justify-center p-4">

            {/* Background Matrix Effect from App.jsx */}
            <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f1f1f_1px,transparent_1px),linear-gradient(to_bottom,#1f1f1f_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20 pointer-events-none" />

            {/* Main Authentication Card */}
            <div className="relative z-10 w-full max-w-sm bg-neutral-900/40 backdrop-blur-md border border-neutral-800/60 rounded-2xl p-8 shadow-2xl">

                <div className="text-center mb-8">
                    <h2 className="text-2xl font-bold tracking-tight text-white">
                        {isLogin ? 'Access Workspace' : 'Initialize Account'}
                    </h2>
                    <p className="text-xs font-mono text-neutral-400 mt-2">
                        codeRAG Core Engine v1.0
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">

                    {/* Conditional Rendering based on wireframe flow */}
                    {isLogin ? (
                        <>
                            <InputField
                                type="text"
                                placeholder="Username or email"
                                value={emailOrUsername}
                                onChange={(e) => setEmailOrUsername(e.target.value)}
                            />
                            <InputField
                                type="password"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </>
                    ) : (
                        <>
                            <InputField
                                type="text"
                                placeholder="Username"
                                value={emailOrUsername}
                                onChange={(e) => setEmailOrUsername(e.target.value)}
                            />
                            <InputField
                                type="email"
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                            <InputField
                                type="password"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <InputField
                                type="password"
                                placeholder="Confirm Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </>
                    )}

                    {/* Primary Action Button */}
                    <button
                        type="submit"
                        className="w-full bg-white text-neutral-950 font-medium text-xs tracking-wide uppercase px-6 py-3.5 rounded-xl hover:bg-neutral-200 active:scale-95 transition-all duration-150 mt-2"
                    >
                        {isLogin ? 'Sign In' : 'Create Account'}
                    </button>
                </form>

                {/* OR Divider (Only visible on Login per wireframe) */}
                {isLogin && (
                    <>
                        <div className="flex items-center space-x-4 my-6">
                            <div className="flex-1 border-t border-neutral-800"></div>
                            <span className="text-xs font-mono text-neutral-500 uppercase tracking-widest">or</span>
                            <div className="flex-1 border-t border-neutral-800"></div>
                        </div>

                        {/* Google OAuth Button */}
                        <button
                            type="button"
                            className="w-full flex items-center justify-center space-x-3 bg-neutral-900 border border-neutral-800 text-neutral-300 font-medium text-xs tracking-wide uppercase px-6 py-3.5 rounded-xl hover:bg-neutral-800 active:scale-95 transition-all duration-150"
                        >
                            <svg className="h-4 w-4" viewBox="0 0 24 24">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                            </svg>
                            <span>Sign in via Google</span>
                        </button>
                    </>
                )}

                {/* Toggle View Link */}
                <div className="mt-8 text-center">
                    <button
                        onClick={() => setIsLogin(!isLogin)}
                        className="text-xs font-mono text-emerald-500/80 hover:text-emerald-400 transition-colors focus:outline-none"
                    >
                        {isLogin ? "Didn't have an account? Sign up" : "Already have an account? Sign in"}
                    </button>
                </div>

            </div>
        </div>
    );
}