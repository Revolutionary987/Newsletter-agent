import React, { useState, useEffect, useRef } from 'react';
import { Download, Sparkles, CheckCircle2, Circle, Loader2, ArrowRight, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
});

function MermaidDiagram({ chart }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current && chart) {
      const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
      mermaid
        .render(id, chart)
        .then(({ svg }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch((err) => console.error('Mermaid rendering error:', err));
    }
  }, [chart]);

  return <div ref={containerRef} className="flex justify-center my-8 overflow-x-auto w-full" />;
}

function ProgressBar({ currentNode }) {
  const PIPELINE_NODES = [
    { id: 'Rewrite_query',       label: 'Structuring topics' },
    { id: 'Deep_research',       label: 'Gathering sources' },
    { id: 'Compressor',          label: 'Distilling information' },
    { id: 'Content_generation',  label: 'Drafting content' },
    { id: 'Hallucination_check', label: 'Reviewing accuracy' },
    { id: 'Image_gen',           label: 'Curating media' },
    { id: 'Rendering Layout',    label: 'Generating PDF layout' },
  ];

  const currentIndex = PIPELINE_NODES.findIndex((n) => n.id === currentNode);

  return (
    <div className="p-8 bg-white border border-slate-200 rounded-2xl shadow-sm max-w-lg mx-auto w-full mt-12 animate-fade-in">
      <h3 className="text-xs uppercase tracking-[0.2em] text-slate-500 font-semibold mb-6 flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
        Building Newsletter
      </h3>
      <div className="space-y-5">
        {PIPELINE_NODES.map((node, idx) => {
          const isDone    = idx < currentIndex;
          const isActive  = idx === currentIndex;
          const isPending = idx > currentIndex;

          return (
            <div key={node.id} className="flex items-center gap-4">
              {isDone ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
              ) : isActive ? (
                <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                  <div className="w-2.5 h-2.5 bg-blue-600 rounded-full animate-pulse" />
                </div>
              ) : (
                <Circle className="w-5 h-5 text-slate-200 flex-shrink-0" />
              )}
              <span
                className={`text-sm tracking-wide ${
                  isDone   ? 'text-slate-600' :
                  isActive ? 'text-slate-900 font-medium' :
                             'text-slate-400'
                }`}
              >
                {node.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function NewsletterGenerator() {
  // Primary States
  const [topic, setTopic] = useState('');
  
  // Configuration States
  const [audience, setAudience] = useState('General Public');
  const [tone, setTone] = useState('Professional & Objective');
  const [length, setLength] = useState('medium');
  const [selectedTemplate, setSelectedTemplate] = useState('YOUR_APITEMPLATE_ID_1');

  // Execution States
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentNode, setCurrentNode] = useState(null);
  const [error, setError] = useState(null);
  
  // Output States
  const [newsletterData, setNewsletterData] = useState(null);
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsGenerating(true);
    setCurrentNode('Rewrite_query');
    setError(null);
    setNewsletterData(null);
    setPdfDownloadUrl(null);

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic,
          audience: audience,
          tone: tone,
          length: length,
          key_points: 'None', 
          template_id: selectedTemplate 
        }),
      });

      if (!response.ok) throw new Error(`Server responded with status ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedData = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          try {
            const jsonStr = line.replace(/^data:\s*/, '');
            const parsedData = JSON.parse(jsonStr);

            if (parsedData.status === 'complete' && parsedData.sections) {
              setNewsletterData(parsedData.sections);
              setPdfDownloadUrl(parsedData.pdf_url);
              setCurrentNode(null);
              hasReceivedData = true;
            } else if (parsedData.status === 'running' && parsedData.node) {
              setCurrentNode(parsedData.node);
            } else if (parsedData.status === 'error') {
              throw new Error(parsedData.detail || 'Pipeline error occurred.');
            }
          } catch (parseErr) {
            console.warn('Skipped unparseable SSE chunk:', line);
          }
        }
      }

      if (!hasReceivedData) throw new Error('Stream completed but no data was received.');

    } catch (err) {
      console.error('Generation error:', err);
      setError(err.message || 'Failed to connect to the server. Please try again.');
    } finally {
      setIsGenerating(false);
      if (!newsletterData) setCurrentNode(null);
    }
  };

  // UI Configuration Arrays
  const audiences = ["General Public", "Tech Enthusiasts", "Executives", "Investors", "Researchers", "Students"];
  const tones = ["Professional & Objective", "Inspiring", "Conversational", "Analytical", "Educational", "Bold & Opinionated"];
  const lengths = [{ id: 'short', label: 'Short' }, { id: 'medium', label: 'Medium' }, { id: 'long', label: 'Long' }, { id: 'deep-dive', label: 'Deep Dive' }];
  const templates = [
    { 
      id: 'YOUR_APITEMPLATE_ID_1', 
      name: 'Aegis Editorial',
      desc: 'Magazine style, high contrast.',
      image: '/template-1.jpg' 
    },
    { 
      id: 'YOUR_APITEMPLATE_ID_2', 
      name: 'Corporate Brief',
      desc: 'Clean columns, navy blue accents.',
      image: '/template-2.jpg'
    },
    { 
      id: 'YOUR_APITEMPLATE_ID_3', 
      name: 'Tech Minimalist',
      desc: 'Stark black & white layout.',
      image: '/template-3.jpg'
    }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans flex flex-col lg:flex-row overflow-hidden">
      
      {/* 💡 INJECTING PREMIUM FONTS */}
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Merriweather:wght@300;400;700;900&display=swap');
        .font-sans  { font-family: 'Plus Jakarta Sans', sans-serif !important; }
        .font-serif { font-family: 'Merriweather', serif !important; }
      `}} />

      {/* LEFT COLUMN: CONTROL PANEL */}
      <div className="w-full lg:w-[480px] xl:w-[540px] bg-white border-r border-slate-200 shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-10 flex flex-col h-screen lg:sticky lg:top-0">
        
        <div className="p-8 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">Workspace</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Publish with Purpose.</h1>
          <p className="text-sm text-slate-500">Craft premium newsletters in minutes.</p>
        </div>

        <div className="flex-1 overflow-y-auto p-8 scrollbar-hide">
          <form onSubmit={handleSubmit} className="space-y-10">
            
            {/* OMNI-PROMPT */}
            <div className="space-y-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400 font-semibold">Newsletter Topic</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="What is this newsletter about? Enter your core subject here..."
                rows={5}
                required
                className="w-full bg-slate-50/50 border border-slate-200 rounded-xl p-5 text-lg text-slate-800 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-all resize-none shadow-inner"
              />
            </div>

            {/* AUDIENCE PILLS */}
            <div className="space-y-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400 font-semibold">Target Audience</label>
              <div className="flex flex-wrap gap-2">
                {audiences.map((aud) => (
                  <button
                    key={aud}
                    type="button"
                    onClick={() => setAudience(aud)}
                    className={`px-4 py-2 text-sm rounded-full transition-all border ${
                      audience === aud 
                        ? 'bg-slate-900 text-white border-slate-900 font-medium shadow-sm' 
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
                    }`}
                  >
                    {aud}
                  </button>
                ))}
              </div>
            </div>

            {/* TONE PILLS */}
            <div className="space-y-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400 font-semibold">Editorial Tone</label>
              <div className="flex flex-wrap gap-2">
                {tones.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTone(t)}
                    className={`px-4 py-2 text-sm rounded-full transition-all border ${
                      tone === t 
                        ? 'bg-slate-900 text-white border-slate-900 font-medium shadow-sm' 
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* LENGTH PILLS */}
            <div className="space-y-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400 font-semibold">Depth & Length</label>
              <div className="flex flex-wrap gap-2">
                {lengths.map((l) => (
                  <button
                    key={l.id}
                    type="button"
                    onClick={() => setLength(l.id)}
                    className={`px-4 py-2 text-sm rounded-full transition-all border ${
                      length === l.id 
                        ? 'bg-slate-900 text-white border-slate-900 font-medium shadow-sm' 
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            {/* VISUAL TEMPLATE GRID */}
            <div className="space-y-3">
              <label className="block text-xs uppercase tracking-widest text-slate-400 font-semibold">Visual Layout</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {templates.map((tmpl) => (
                  <button
                    key={tmpl.id}
                    type="button"
                    onClick={() => setSelectedTemplate(tmpl.id)}
                    className={`relative overflow-hidden text-left rounded-xl transition-all border flex flex-col h-40 group ${
                      selectedTemplate === tmpl.id
                        ? 'ring-2 ring-blue-600 border-transparent shadow-md'
                        : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
                    }`}
                  >
                    <div className="h-20 w-full bg-slate-100 border-b border-slate-100 overflow-hidden relative">
                      <img 
                        src={tmpl.image} 
                        alt={tmpl.name} 
                        className="w-full h-full object-cover object-top transition-transform duration-500 group-hover:scale-105" 
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentElement.classList.add('bg-slate-200');
                        }}
                      />
                      {selectedTemplate === tmpl.id && (
                        <div className="absolute top-2 right-2 bg-blue-600 text-white rounded-full p-0.5 shadow-sm">
                          <CheckCircle2 className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                    <div className={`p-3 flex-1 flex flex-col justify-between transition-colors ${selectedTemplate === tmpl.id ? 'bg-blue-50/50' : 'bg-white'}`}>
                      <span className={`text-sm font-bold truncate ${selectedTemplate === tmpl.id ? 'text-blue-900' : 'text-slate-800'}`}>
                        {tmpl.name}
                      </span>
                      <span className={`text-[10px] line-clamp-1 ${selectedTemplate === tmpl.id ? 'text-blue-700/80' : 'text-slate-500'}`}>
                        {tmpl.desc}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

          </form>
        </div>

        {/* STICKY FOOTER TRIGGER */}
        <div className="p-6 border-t border-slate-100 bg-white/80 backdrop-blur-md flex-shrink-0">
           <button
             onClick={handleSubmit}
             disabled={isGenerating || !topic.trim()}
             className="w-full h-14 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm uppercase tracking-widest rounded-xl shadow-[0_8px_20px_-6px_rgba(37,99,235,0.4)] disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3"
           >
             {isGenerating ? (
               <>
                 <Loader2 className="w-5 h-5 animate-spin" />
                 Generating...
               </>
             ) : (
               <>
                 Generate Newsletter
                 <ArrowRight className="w-5 h-5" />
               </>
             )}
           </button>
        </div>

      </div>

      {/* RIGHT COLUMN: OUTPUT STAGE */}
      <div className="flex-1 h-screen overflow-y-auto bg-[#F8FAFC] relative scroll-smooth">
        
        <div className="max-w-4xl mx-auto p-6 md:p-12 lg:p-16">
          
          {error && (
            <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl flex items-start gap-3">
              <span className="font-bold">Error:</span> {error}
            </div>
          )}

          {/* EMPTY STATE */}
          {!isGenerating && !newsletterData && !error && (
            <div className="h-full min-h-[60vh] flex flex-col items-center justify-center text-center opacity-60">
              <div className="w-20 h-20 bg-slate-200 rounded-full flex items-center justify-center mb-6">
                <FileText className="w-8 h-8 text-slate-400" />
              </div>
              <h2 className="text-xl font-medium text-slate-900 mb-2">Ready to Create</h2>
              <p className="text-slate-500 max-w-sm">Set your preferences and enter a topic to start drafting your newsletter.</p>
            </div>
          )}

          {/* PROGRESS STATE */}
          {isGenerating && <ProgressBar currentNode={currentNode} />}

          {/* FINAL RESULTS */}
          {newsletterData && !isGenerating && (
            <div className="animate-fade-in space-y-8">
              
              {/* PDF DOWNLOAD BAR */}
              {pdfDownloadUrl && (
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4 mb-8">
                  <div>
                    <h3 className="font-bold text-slate-900 text-lg">Your Document is Ready</h3>
                    <p className="text-sm text-slate-500">Premium layout rendered successfully.</p>
                  </div>
                  <a
                    href={pdfDownloadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-6 py-3.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold uppercase tracking-widest rounded-xl transition-all shadow-md flex-shrink-0"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </a>
                </div>
              )}

              {/* MARKDOWN PREVIEW */}
              <div className="bg-white border border-slate-200 rounded-3xl p-8 md:p-14 shadow-sm">
                <div className="mb-12 border-b border-slate-100 pb-8 text-center">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400 block mb-4 font-sans">Live Preview</span>
                  <h1 className="text-4xl md:text-5xl font-serif font-bold text-slate-900 leading-tight">{topic}</h1>
                </div>

                {newsletterData.map((section, index) => (
                  <div key={index} className="mb-14 last:mb-0">
                    <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-900 mb-6 pb-4 border-b border-slate-100">
                      {section.section_title}
                    </h2>

                    {section.image_url && (
                      <div className="mb-8 group">
                        <div className="overflow-hidden rounded-2xl border border-slate-100 bg-slate-50">
                          <img
                            src={section.image_url}
                            alt={section.alt_text || section.section_title}
                            referrerPolicy="no-referrer"
                            crossOrigin="anonymous"
                            className="w-full h-auto object-cover max-h-[500px] transition-transform duration-700 group-hover:scale-[1.02]"
                          />
                        </div>
                        {section.alt_text && (
                          <p className="text-xs text-slate-500 mt-3 text-center italic font-sans">
                            {section.alt_text}
                            {section.image_source && <span className="uppercase tracking-wider opacity-60 ml-2">— {section.image_source}</span>}
                          </p>
                        )}
                      </div>
                    )}

                    <div className="prose prose-slate prose-lg max-w-none text-slate-700 leading-relaxed font-serif">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ node, inline, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || '');
                            if (!inline && match && match[1] === 'mermaid') {
                              return <MermaidDiagram chart={String(children).replace(/\n$/, '')} />;
                            }
                            return (
                              <code className={`bg-slate-100 px-1.5 py-0.5 rounded-md text-[0.9em] font-mono text-slate-800 ${className || ''}`} {...props}>
                                {children}
                              </code>
                            );
                          },
                          table: ({ node, ...props }) => (
                            <div className="overflow-x-auto my-10 border border-slate-200 rounded-xl shadow-sm font-sans">
                              <table className="min-w-full divide-y divide-slate-200 m-0" {...props} />
                            </div>
                          ),
                          thead: ({ node, ...props }) => <thead className="bg-slate-50" {...props} />,
                          th: ({ node, ...props }) => <th className="px-6 py-4 text-left text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-200" {...props} />,
                          td: ({ node, ...props }) => <td className="whitespace-normal px-6 py-4 text-sm text-slate-700 border-b border-slate-100" {...props} />,
                          a: ({ node, ...props }) => <a className="text-blue-600 hover:text-blue-800 underline decoration-blue-200 underline-offset-4 font-medium transition-colors" {...props} />,
                          h3: ({ node, ...props }) => <h3 className="text-xl font-bold text-slate-900 mt-10 mb-4 font-serif" {...props} />,
                          h4: ({ node, ...props }) => <h4 className="text-lg font-semibold text-slate-900 mt-8 mb-3 font-serif" {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc pl-6 space-y-3 my-6 text-slate-700 marker:text-blue-400" {...props} />,
                          li: ({ node, ...props }) => <li className="pl-2" {...props} />,
                          p: ({ node, ...props }) => <p className="my-6" {...props} />,
                          strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900" {...props} />
                        }}
                      >
                        {section.paragraph_text}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}