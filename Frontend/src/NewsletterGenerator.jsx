import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
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

// --- Progress indicator component ---
function ProgressBar({ currentNode }) {
  const PIPELINE_NODES = [
    { id: 'Rewrite_query',       label: 'Planning research' },
    { id: 'Deep_research',       label: 'Deep research' },
    { id: 'Compressor',          label: 'Compressing data' },
    { id: 'Content_generation',  label: 'Writing draft' },
    { id: 'Hallucination_check', label: 'Fact checking' },
    { id: 'Image_gen',           label: 'Generating images' },
    { id: 'Final_check',         label: 'Final review' },
  ];

  const currentIndex = PIPELINE_NODES.findIndex((n) => n.id === currentNode);

  return (
    <div className="mt-8 p-6 bg-white border border-slate-200 rounded-sm">
      <p className="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-4">
        Pipeline Status
      </p>
      <div className="space-y-2">
        {PIPELINE_NODES.map((node, idx) => {
          const isDone    = idx < currentIndex;
          const isActive  = idx === currentIndex;
          const isPending = idx > currentIndex;
          return (
            <div key={node.id} className="flex items-center gap-3">
              <div
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  isDone   ? 'bg-emerald-500' :
                  isActive ? 'bg-slate-900 animate-pulse' :
                             'bg-slate-200'
                }`}
              />
              <span
                className={`text-sm ${
                  isDone   ? 'text-emerald-600' :
                  isActive ? 'text-slate-900 font-medium' :
                             'text-slate-400'
                }`}
              >
                {node.label}
                {isActive && '…'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function NewsletterGenerator() {
  const [topic,        setTopic]        = useState('');
  const [audience,     setAudience]     = useState('');
  const [tone,         setTone]         = useState('');
  const [length,       setLength]       = useState('');
  const [keyPoints,    setKeyPoints]    = useState('');
  const [instructions, setInstructions] = useState('');

  const [isGenerating,   setIsGenerating]   = useState(false);
  const [currentNode,    setCurrentNode]    = useState(null);
  const [error,          setError]          = useState(null);
  const [newsletterData, setNewsletterData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setCurrentNode('Rewrite_query');
    setError(null);
    setNewsletterData(null);

    let enrichedTopic = topic;
    if (instructions) enrichedTopic += `. Extra instructions: ${instructions}.`;

    const API_BASE_URL =
      import.meta.env.VITE_API_URL || 'https://aicoder35235-newsletter.hf.space';

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic:      enrichedTopic,
          // ✅ FIX: send exact keys the backend AUDIENCE_STYLE / TONE_INSTRUCTIONS dicts expect
          audience:   audience   || 'General Public',
          tone:       tone       || 'Professional & Objective',
          length:     length     || 'medium',
          key_points: keyPoints  || 'None',
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedData = false;

      // ✅ FIX: while loop + hasReceivedData check placed correctly OUTSIDE the loop
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          try {
            const jsonStr    = line.replace(/^data:\s*/, '');
            const parsedData = JSON.parse(jsonStr);

            if (parsedData.status === 'complete' && parsedData.sections) {
              // ✅ FIX: server now sends { status: 'complete', sections: [...] }
              setNewsletterData(parsedData.sections);
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
      } // ✅ while closes here — hasReceivedData check is now after the loop

      if (!hasReceivedData) {
        throw new Error('Stream completed but no newsletter data was received.');
      }

    } catch (err) {
      console.error('Generation error:', err);
      setError(err.message || 'Failed to connect to the AI Engine. Please try again.');
    } finally {
      setIsGenerating(false);
      setCurrentNode(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9F9F6] text-slate-900 font-sans p-6 md:p-12 flex flex-col items-center justify-center">
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');
        .font-serif { font-family: 'Playfair Display', serif; }
        .font-sans  { font-family: 'Inter', sans-serif; }
      `}} />

      <div className="w-full max-w-3xl">

        {/* Header */}
        <div className="text-center mb-12">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-3 font-medium">
            Editorial Studio
          </p>
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-slate-900 mb-4 tracking-tight">
            Curate the narrative.
          </h1>
          <p className="text-slate-500 text-lg">
            High-end, autonomous newsletter generation.
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-sm border border-slate-200/60 shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] p-8 md:p-12">
          <form onSubmit={handleSubmit} className="space-y-10">

            {/* Topic */}
            <div className="space-y-2">
              <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                What should this newsletter be about?
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter your topic..."
                className="w-full bg-transparent border-b border-gray-300 py-3 text-xl md:text-2xl text-slate-900 placeholder:text-slate-300 focus:outline-none focus:border-slate-900 transition-colors"
                required
              />
            </div>

            {/* Audience + Tone */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

              <div className="space-y-2">
                <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                  Target Audience
                </label>
                <div className="relative">
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                    className="w-full bg-transparent border-b border-gray-300 py-3 text-slate-800 appearance-none focus:outline-none focus:border-slate-900 transition-colors cursor-pointer rounded-none"
                    required
                  >
                    <option value="" disabled>Select audience...</option>
                    {/* ✅ FIX: values match exact AUDIENCE_STYLE keys in the backend */}
                    <option value="General Public">General Public</option>
                    <option value="Tech Enthusiasts">Tech Enthusiasts</option>
                    <option value="Executives">Executives</option>
                    <option value="Students">Students</option>
                    <option value="Investors">Investors</option>
                    <option value="Researchers">Researchers</option>
                  </select>
                  <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                  Editorial Tone
                </label>
                <div className="relative">
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full bg-transparent border-b border-gray-300 py-3 text-slate-800 appearance-none focus:outline-none focus:border-slate-900 transition-colors cursor-pointer rounded-none"
                    required
                  >
                    <option value="" disabled>Select tone...</option>
                    {/* ✅ FIX: values match exact TONE_INSTRUCTIONS keys in the backend */}
                    <option value="Professional & Objective">Professional & Objective</option>
                    <option value="Inspiring">Inspiring</option>
                    <option value="Conversational">Conversational</option>
                    <option value="Analytical">Analytical</option>
                    <option value="Educational">Educational</option>
                    <option value="Bold & Opinionated">Bold & Opinionated</option>
                  </select>
                  <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>
            </div>

            {/* Length Toggles */}
            <div className="space-y-4">
              <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                Approximate Length
              </label>
              <div className="flex flex-wrap gap-3">
                {[
                  { id: 'short',     label: 'Short',     desc: '500–700 words'  },
                  { id: 'medium',    label: 'Medium',    desc: '900–1200 words' },
                  { id: 'long',      label: 'Long',      desc: '1500–2000 words'},
                  { id: 'deep-dive', label: 'Deep-dive', desc: '2500+ words'    },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setLength(opt.id)}
                    className={`px-4 py-2 text-sm border transition-all rounded-sm ${
                      length === opt.id
                        ? 'border-slate-900 text-slate-900 bg-slate-50/50 font-medium'
                        : 'border-gray-200 text-slate-500 hover:border-gray-300'
                    }`}
                  >
                    {opt.label}: <span className="font-normal">{opt.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Key Points */}
            <div className="space-y-2">
              <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                Key Points to Cover
              </label>
              <textarea
                value={keyPoints}
                onChange={(e) => setKeyPoints(e.target.value)}
                placeholder="What are the essential arguments or updates?"
                rows={4}
                className="w-full bg-transparent border border-gray-300 p-4 text-slate-800 placeholder:text-slate-300 focus:outline-none focus:border-slate-900 transition-colors rounded-sm resize-none"
              />
            </div>

            {/* Additional Instructions */}
            <div className="space-y-2">
              <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                Additional Instructions{' '}
                <span className="text-slate-400 font-normal normal-case tracking-normal ml-1">
                  (Optional)
                </span>
              </label>
              <textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Any specific sources, quotes, or stylistic requests?"
                rows={3}
                className="w-full bg-transparent border border-gray-300 p-4 text-slate-800 placeholder:text-slate-300 focus:outline-none focus:border-slate-900 transition-colors rounded-sm resize-none"
              />
            </div>

            {/* Submit */}
            <div className="pt-6">
              <button
                type="submit"
                disabled={isGenerating}
                className="w-full md:w-auto px-10 py-4 border border-slate-900 bg-transparent text-slate-900 uppercase tracking-[0.2em] text-xs font-semibold hover:bg-slate-900 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed rounded-none"
              >
                {isGenerating ? 'GENERATING...' : 'GENERATE NEWSLETTER'}
              </button>
            </div>
          </form>
        </div>

        {/* Pipeline progress */}
        {isGenerating && <ProgressBar currentNode={currentNode} />}

        {/* Error */}
        {error && (
          <div className="mt-8 p-4 bg-red-50 border border-red-200 text-red-600 text-sm rounded-sm">
            {error}
          </div>
        )}

        {/* Newsletter output */}
        {newsletterData && (
          <div className="mt-16 bg-white border border-slate-200 p-8 md:p-12 shadow-sm">
            {newsletterData.map((section, index) => (
              <div key={index} className="mb-12 last:mb-0">
                <h2 className="text-3xl font-serif font-bold text-slate-900 mb-6 pb-2 border-b border-slate-100">
                  {section.section_title}
                </h2>

                {section.image_url && (
                  <div className="mb-8">
                    <img
                      src={section.image_url}
                      alt={section.alt_text || section.section_title}
                      className="w-full h-auto object-cover rounded-sm shadow-sm"
                    />
                    {section.alt_text && (
                      <p className="text-xs text-slate-400 mt-3 text-center italic tracking-wide">
                        {section.alt_text}
                        {section.image_source && ` (via ${section.image_source})`}
                      </p>
                    )}
                  </div>
                )}

                <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        if (!inline && match && match[1] === 'mermaid') {
                          return (
                            <MermaidDiagram
                              chart={String(children).replace(/\n$/, '')}
                            />
                          );
                        }
                        return (
                          <code
                            className={`bg-slate-100 px-1.5 py-0.5 rounded text-sm font-mono text-slate-800 ${className || ''}`}
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      },
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-8 border border-slate-200 rounded-sm">
                          <table className="min-w-full divide-y divide-slate-200" {...props} />
                        </div>
                      ),
                      thead: ({ node, ...props }) => (
                        <thead className="bg-slate-50" {...props} />
                      ),
                      th: ({ node, ...props }) => (
                        <th
                          className="px-4 py-3 text-left text-xs font-semibold text-slate-900 uppercase tracking-wider"
                          {...props}
                        />
                      ),
                      td: ({ node, ...props }) => (
                        <td
                          className="whitespace-normal px-4 py-4 text-sm text-slate-600 border-t border-slate-200"
                          {...props}
                        />
                      ),
                      a: ({ node, ...props }) => (
                        <a
                          className="text-blue-600 hover:text-blue-800 underline decoration-blue-200 underline-offset-2"
                          {...props}
                        />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3
                          className="text-xl font-bold text-slate-900 mt-8 mb-4"
                          {...props}
                        />
                      ),
                      h4: ({ node, ...props }) => (
                        <h4
                          className="text-lg font-semibold text-slate-900 mt-6 mb-3"
                          {...props}
                        />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul
                          className="list-disc pl-5 space-y-2 my-4 marker:text-slate-400"
                          {...props}
                        />
                      ),
                      p: ({ node, ...props }) => <p className="my-4" {...props} />,
                    }}
                  >
                    {section.paragraph_text}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
