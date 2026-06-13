import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function PDFTemplate({ newsletterData, topic }) {
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  if (!newsletterData) return null;

  return (
    // A4 Canvas: Pure white background, strict print dimensions
    <div className="w-[210mm] min-h-[297mm] bg-white text-slate-900 p-12 font-sans antialiased">
      
      {/* 1. THE CORPORATE MASTHEAD */}
      <div className="border-t-8 border-blue-700 pt-6 mb-14">
        <div className="flex justify-between items-end mb-8">
          <div>
            {/* Embedded custom branding */}
            <h2 className="text-2xl font-black tracking-tighter text-blue-700 uppercase">
              Aegis
            </h2>
            <p className="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase mt-1">
              Market Intelligence
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">
              {currentDate} <span className="mx-2">|</span> Edition 1
            </p>
          </div>
        </div>
        
        {/* Massive, constrained-width title to mimic premium publications */}
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.1] w-4/5 capitalize">
          {topic || 'Strategic Tech & Market Briefing'}
        </h1>
      </div>

      {/* 2. THE CONTENT STREAM */}
      <div className="space-y-16">
        {newsletterData.map((section, index) => (
          <div key={index} className="break-inside-avoid print-section">
            
            {/* 3. GIANT NUMBERED ANCHORS */}
            <div className="flex items-start gap-5 mb-8">
              <span className="text-5xl font-black text-blue-600 leading-none tracking-tighter opacity-90">
                {String(index + 1).padStart(2, '0')}
              </span>
              <h2 className="text-3xl font-bold text-slate-900 leading-tight pt-1">
                {section.section_title}
              </h2>
            </div>

            {/* 4. MULTI-COLUMN MAGAZINE LAYOUT */}
            {section.image_url ? (
              <div className="grid grid-cols-12 gap-8 items-start">
                {/* Text Column */}
                <div className="col-span-7 text-[13px] leading-relaxed text-slate-700 text-justify prose prose-slate max-w-none">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {section.paragraph_text}
                  </ReactMarkdown>
                </div>
                {/* Image Column */}
                <div className="col-span-5 shrink-0">
                  <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 shadow-sm">
                    <img
                      src={section.image_url}
                      alt={section.alt_text || section.section_title}
                      className="w-full h-auto object-cover rounded-lg"
                    />
                  </div>
                  {section.alt_text && (
                    <p className="text-[10px] text-slate-400 mt-3 text-right italic font-medium">
                      {section.alt_text}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              // Full Width Layout
              <div className="text-[13px] leading-relaxed text-slate-700 text-justify prose prose-slate max-w-none">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {section.paragraph_text}
                </ReactMarkdown>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 5. PERMANENT DOCUMENT FOOTER */}
      <div className="mt-20 pt-6 border-t-2 border-slate-900 flex justify-between items-center text-[9px] uppercase tracking-widest text-slate-500 font-bold">
        <p>Aegis Autonomous Research Engine</p>
        <p>Confidential • Internal Distribution Only</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 🎨 CUSTOM MARKDOWN RENDERERS: The Secret to the "Premium" Look
// We intercept standard markdown tags and inject heavy, structural Tailwind CSS.
// ---------------------------------------------------------------------------
const markdownComponents = {
  // BENTO BOX LISTS: Converts standard bullet points into a grid of premium cards
  ul: ({ node, ...props }) => (
    <ul className="grid grid-cols-2 gap-4 my-8 p-0 list-none" {...props} />
  ),
  li: ({ node, ...props }) => (
    <li className="bg-slate-50 p-4 rounded-lg border border-slate-200 shadow-sm text-xs font-medium text-slate-800 leading-snug relative pl-10" {...props}>
      <span className="absolute left-4 top-4 w-4 h-4 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-[10px] font-bold">
        ✓
      </span>
      {props.children}
    </li>
  ),
  // EDGE-TO-EDGE DATA TABLES: Strict corporate styling, removing vertical lines
  table: ({ node, ...props }) => (
    <div className="w-full my-10 border-t-[3px] border-slate-900">
      <table className="min-w-full text-xs text-left border-collapse" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => (
    <thead className="border-b-2 border-slate-200 bg-white text-slate-900" {...props} />
  ),
  th: ({ node, ...props }) => (
    <th className="py-4 font-bold uppercase tracking-widest text-[10px]" {...props} />
  ),
  td: ({ node, ...props }) => (
    <td className="py-4 border-b border-slate-100 text-slate-700 align-top pr-6" {...props} />
  ),
  // CLEANER SUBHEADERS
  h3: ({ node, ...props }) => (
    <h3 className="text-lg font-bold text-slate-900 mt-8 mb-3 tracking-tight" {...props} />
  ),
  h4: ({ node, ...props }) => (
    <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider mt-6 mb-2" {...props} />
  ),
  // SUBTLE QUOTES
  blockquote: ({ node, ...props }) => (
    <blockquote className="border-l-4 border-blue-500 pl-5 my-6 italic text-slate-600 bg-slate-50 py-3 rounded-r-lg font-serif text-sm" {...props} />
  ),
  p: ({ node, ...props }) => <p className="my-4" {...props} />
};