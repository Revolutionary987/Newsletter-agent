import React, { useState, useEffect } from 'react';
import { Loader2, Send, Sparkles, Image as ImageIcon, BookOpen, User } from 'lucide-react';

const NewsletterGenerator = () => {
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('General Public');
  const [tone, setTone] = useState('Professional');
  
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('Initializing AI agents...');
  const [newsletterData, setNewsletterData] = useState(null);
  const [error, setError] = useState(null);

  // Array of dynamic loading messages to keep the user engaged
  const loadingMessages = [
    'Researching the latest on this topic...',
    'Analyzing audience demographics...',
    'Structuring the narrative flow...',
    'Drafting compelling paragraphs...',
    'Generating high-quality visuals...',
    'Fact-checking and refining the content...',
    'Applying the final polish...'
  ];

  useEffect(() => {
    let interval;
    if (loading) {
      let step = 0;
      interval = setInterval(() => {
        step = (step + 1) % loadingMessages.length;
        setLoadingText(loadingMessages[step]);
      }, 4500); // Changes text every 4.5 seconds
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError(null);
    setNewsletterData(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic, audience, tone }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate newsletter. Please check if the backend is running.');
      }

      const data = await response.json();
      
      if (data.status === 'success' && data.data) {
        setNewsletterData(data.data);
      } else {
        throw new Error('Invalid response format from server.');
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F7F4] text-slate-900 font-sans selection:bg-slate-200 selection:text-slate-900">
      
      {/* 1. The Hero Section (Input Form) */}
      <div className="bg-[#F7F7F4] border-b border-slate-200 relative overflow-hidden">

        <div className="max-w-5xl mx-auto px-4 py-16 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="uppercase tracking-[0.3em] text-xs font-semibold text-slate-400 mb-6 block">
              Editorial Studio
            </span>
            <h1 className="text-5xl md:text-7xl font-serif text-slate-900 mb-6 leading-tight">
              Curate the narrative.
            </h1>
            <p className="text-lg md:text-xl text-slate-500 font-light max-w-2xl mx-auto">
              High-end, autonomous newsletter generation.
            </p>
          </div>

          <div className="bg-white p-8 md:p-14 border border-slate-200">
            <form onSubmit={handleGenerate} className="space-y-8">
              <div>
                <label htmlFor="topic" className="block text-sm font-semibold text-slate-700 mb-3 tracking-wide">
                  WHAT SHOULD THIS NEWSLETTER BE ABOUT?
                </label>
                <div className="relative group">
                  <input
                    type="text"
                    id="topic"
                    className="block w-full px-0 py-4 text-3xl md:text-4xl font-light border-0 border-b-2 border-slate-200 focus:ring-0 focus:border-slate-900 bg-transparent transition-all outline-none placeholder:text-slate-300 placeholder:font-light"
                    placeholder="Enter your topic..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <label htmlFor="audience" className="block text-sm font-semibold text-slate-700 mb-3 tracking-wide">
                    TARGET AUDIENCE
                  </label>
                  <div className="relative">
                    <select
                      id="audience"
                      className="block w-full pl-0 pr-10 py-4 text-base border-0 border-b-2 border-slate-200 focus:ring-0 focus:border-slate-900 bg-transparent appearance-none font-medium text-slate-700 outline-none transition-all cursor-pointer"
                      value={audience}
                      onChange={(e) => setAudience(e.target.value)}
                    >
                      <option>General Public</option>
                      <option>Industry Experts</option>
                      <option>Investors & Stakeholders</option>
                      <option>Students & Academics</option>
                      <option>C-Suite Executives</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-900">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="tone" className="block text-sm font-semibold text-slate-700 mb-3 tracking-wide">
                    EDITORIAL TONE
                  </label>
                  <div className="relative">
                    <select
                      id="tone"
                      className="block w-full pl-0 pr-10 py-4 text-base border-0 border-b-2 border-slate-200 focus:ring-0 focus:border-slate-900 bg-transparent appearance-none font-medium text-slate-700 outline-none transition-all cursor-pointer"
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                    >
                      <option>Professional & Objective</option>
                      <option>Conversational & Engaging</option>
                      <option>Academic & Analytical</option>
                      <option>Witty & Entertaining</option>
                      <option>Urgent & News-focused</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-900">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 flex justify-center">
                <button
                  type="submit"
                  disabled={loading || !topic.trim()}
                  className="w-full md:w-auto flex items-center justify-center py-3.5 px-10 text-xs uppercase tracking-[0.2em] font-semibold border border-slate-900 text-slate-900 bg-transparent hover:bg-slate-900 hover:text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-500"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                      Synthesizing...
                    </>
                  ) : (
                    <>
                      Generate Newsletter
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-4xl mx-auto px-4 py-16 sm:px-6 lg:px-8 min-h-[60vh]">
        
        {/* Error State */}
        {error && (
          <div className="rounded-2xl bg-red-50 p-6 border border-red-100 mb-8 flex items-start animate-in slide-in-from-top-4">
            <svg className="h-6 w-6 text-red-500 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="ml-4">
              <h3 className="text-sm font-semibold text-red-800 uppercase tracking-wider">Connection Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 2. The Waiting Experience (Loading State) */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 animate-in fade-in duration-700">
            <div className="relative mb-12">
              <div className="absolute inset-0 rounded-full blur-2xl bg-indigo-500/20 animate-pulse"></div>
              <div className="relative w-32 h-32 rounded-full border-t-2 border-indigo-600 shadow-[0_0_40px_rgba(79,70,229,0.2)] animate-spin flex items-center justify-center bg-white/50 backdrop-blur-sm">
                <div className="w-20 h-20 rounded-full border-b-2 border-blue-500 animate-[spin_2s_linear_reverse] flex items-center justify-center">
                  <Sparkles className="h-8 w-8 text-indigo-500 animate-pulse" />
                </div>
              </div>
            </div>
            
            <div className="text-center space-y-4 max-w-lg w-full">
              <div className="h-8 relative overflow-hidden flex justify-center">
                <h2 key={loadingText} className="text-2xl font-bold text-slate-800 tracking-tight absolute animate-in slide-in-from-bottom-5 fade-in duration-500">
                  {loadingText}
                </h2>
              </div>
              <p className="text-slate-500 text-lg">
                Please wait while our LangGraph agents synthesize information. This deep-dive takes about 30-60 seconds.
              </p>
            </div>
            
            {/* Elegant Skeleton Presentation Layout */}
            <div className="w-full mt-24 space-y-20 opacity-30 pointer-events-none">
              {[1, 2].map((i) => (
                <div key={i} className="animate-pulse flex flex-col space-y-8">
                  <div className="h-[400px] bg-gradient-to-tr from-slate-200 to-slate-100 rounded-3xl w-full"></div>
                  <div className="px-4 md:px-12 space-y-6">
                    <div className="h-12 bg-slate-200 rounded-lg w-3/4"></div>
                    <div className="space-y-4 pt-4">
                      <div className="h-4 bg-slate-200 rounded w-full"></div>
                      <div className="h-4 bg-slate-200 rounded w-full"></div>
                      <div className="h-4 bg-slate-200 rounded w-11/12"></div>
                      <div className="h-4 bg-slate-200 rounded w-5/6"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. The Presentation Layer (The Output) */}
        {!loading && newsletterData && newsletterData.length > 0 && (
          <div className="space-y-20 lg:space-y-32 animate-in fade-in slide-in-from-bottom-12 duration-1000">
            
            {/* Magazine Header */}
            <header className="text-center pb-12 border-b-2 border-slate-900">
              <span className="uppercase tracking-[0.2em] text-xs font-bold text-indigo-600 mb-6 block">
                The Daily AI Synthesis
              </span>
              <h2 className="text-5xl md:text-7xl font-black text-slate-900 font-serif leading-none tracking-tight mb-8">
                {topic}
              </h2>
              <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-medium text-slate-500 uppercase tracking-wider">
                <span className="flex items-center"><User className="w-4 h-4 mr-2"/> Audience: {audience}</span>
                <span className="hidden sm:inline text-slate-300">•</span>
                <span className="flex items-center"><BookOpen className="w-4 h-4 mr-2"/> Tone: {tone}</span>
                <span className="hidden sm:inline text-slate-300">•</span>
                <span className="flex items-center">Edition: {new Date().toLocaleDateString()}</span>
              </div>
            </header>

            {/* Articles Mapping */}
            {newsletterData.map((section, index) => (
              <article key={index} className="group relative">
                
                {section.image_url ? (
                  <figure className="mb-12 overflow-hidden rounded-[2rem] shadow-2xl ring-1 ring-slate-900/5 transition-transform duration-700 ease-out">
                    <img
                      src={section.image_url}
                      alt={section.alt_text || section.section_title}
                      className="w-full h-auto md:h-[600px] object-cover transition-transform duration-[1.5s] ease-out group-hover:scale-[1.03]"
                      loading="lazy"
                    />
                    {section.alt_text && (
                      <figcaption className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-6 pt-16 text-white/80 text-sm font-medium">
                        {section.alt_text}
                      </figcaption>
                    )}
                  </figure>
                ) : (
                  <div className="mb-12 w-full h-64 bg-slate-100 rounded-[2rem] flex items-center justify-center text-slate-300 ring-1 ring-slate-900/5">
                    <ImageIcon className="w-16 h-16 opacity-30" />
                  </div>
                )}
                
                <div className="max-w-[45rem] mx-auto px-4 sm:px-0">
                  <h3 className="text-4xl md:text-5xl font-bold text-slate-900 mb-8 font-serif leading-[1.1] tracking-tight">
                    {section.section_title}
                  </h3>
                  
                  {/* High-end Editorial Typography */}
                  <div className="prose prose-xl md:prose-2xl prose-slate max-w-none text-slate-700 leading-relaxed font-serif">
                    {section.paragraph_text.split('\n\n').map((paragraph, pIndex) => (
                      <p 
                        key={pIndex} 
                        className={`mb-8 ${pIndex === 0 
                          ? 'first-letter:text-7xl first-letter:font-black first-letter:text-slate-900 first-letter:float-left first-letter:mr-4 first-letter:mt-2 first-line:uppercase first-line:tracking-widest first-line:font-semibold first-line:text-slate-900' 
                          : ''}`}
                      >
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
                
                {/* Decorative separator between sections except the last one */}
                {index < newsletterData.length - 1 && (
                  <div className="flex items-center justify-center mt-20 opacity-30">
                    <div className="w-16 h-px bg-slate-900"></div>
                    <Sparkles className="w-5 h-5 mx-4 text-slate-900" />
                    <div className="w-16 h-px bg-slate-900"></div>
                  </div>
                )}
              </article>
            ))}
            
            {/* Magazine Footer */}
            <footer className="pt-24 pb-12 text-center border-t border-slate-200 mt-24">
              <Sparkles className="w-8 h-8 mx-auto text-slate-300 mb-6" />
              <p className="text-slate-500 italic font-serif text-xl">
                Generated entirely by artificial intelligence.
              </p>
            </footer>
          </div>
        )}

        {/* Empty State */}
        {!loading && !newsletterData && !error && (
          <div className="text-center py-32 text-slate-400">
            <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookOpen className="h-10 w-10 text-slate-300" />
            </div>
            <p className="text-xl font-medium text-slate-500">Your editorial piece awaits.</p>
            <p className="mt-2">Enter a topic above to begin generating.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsletterGenerator;
