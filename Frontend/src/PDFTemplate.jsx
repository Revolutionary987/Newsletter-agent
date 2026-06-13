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
    // Clean, structured A4 boundary layout using strict HEX spacing safely clear of oklch bugs
    <div className="w-[210mm] min-h-[297mm] bg-[#ffffff] text-[#1e293b] p-16 font-sans antialiased mx-auto">
      
      {/* 🏙️ PREMIUM SAAS INSTITUTIONAL MASTHEAD */}
      <div className="border-b border-[#e2e8f0] pb-8 mb-12 flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="w-3 h-3 bg-[#2563eb] rounded-sm" />
            <span className="text-xs font-black uppercase tracking-[0.25em] text-[#0f172a]">
              Aegis Studio
            </span>
          </div>
          <p className="text-[10px] font-bold tracking-[0.1em] text-[#94a3b8] uppercase">
            Market Intelligence Engine
          </p>
        </div>
        <div className="text-right">
          <p className="text-[11px] font-bold text-[#64748b] bg-[#f1f5f9] px-3 py-1 rounded-sm uppercase tracking-wider inline-block">
            {currentDate} <span className="mx-1.5 text-[#cbd5e1]">|</span> Briefing 01
          </p>
        </div>
      </div>

      {/* DYNAMIC HERO CARD */}
      <div className="bg-[#f8fafc] border border-[#e2e8f0] p-8 rounded-sm mb-12">
        <span className="text-[10px] font-bold tracking-widest text-[#2563eb] uppercase bg-[#dbeafe] px-2 py-0.5 rounded-sm">
          Executive Document
        </span>
        <h1 className="text-4xl font-extrabold tracking-tight text-[#0f172a] mt-3 mb-4 capitalize leading-tight break-words">
          {topic || 'Strategic Market Briefing'}
        </h1>
        <p className="text-xs text-[#64748b] max-w-xl leading-relaxed break-words">
          Automated meta-synthesis of current market data indicators, vendor performance targets, and strategic architecture parameters compiled across live infrastructure vectors.
        </p>
      </div>

      {/* 📚 THE EDITORIAL INTERACTIVE LAYER */}
      <div className="space-y-16">
        {newsletterData.map((section, index) => {
          // Alternates media alignments dynamically to match corporate editorial style guide standards
          const isEven = index % 2 === 0;

          return (
            <div key={index} className="break-inside-avoid border-b border-[#f1f5f9] pb-12 last:border-0">
              
              {/* SECTION KEYBOARD LINK HEADER */}
              <div className="flex items-baseline gap-3 mb-6">
                <span className="text-xs font-mono font-bold text-[#2563eb] bg-[#eff6ff] border border-[#dbeafe] px-2 py-0.5 rounded-sm">
                  SECTION {String(index + 1).padStart(2, '0')}
                </span>
                <h2 className="text-2xl font-bold text-[#0f172a] tracking-tight break-words">
                  {section.section_title}
                </h2>
              </div>

              {/* DYNAMIC STRUCTURAL COLUMN MATRIX */}
              {section.image_url ? (
                <div className="flex flex-col gap-6">
                  {/* Asymmetric Alternating Media Split */}
                  <div className={`flex flex-col md:flex-row gap-8 items-start ${isEven ? '' : 'md:flex-row-reverse'}`}>
                    
                    {/* Core Prose Node */}
                    <div className="w-full md:w-3/5 text-[13px] leading-relaxed text-[#475569] text-justify">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={markdownComponents}
                      >
                        {section.paragraph_text}
                      </ReactMarkdown>
                    </div>

                    {/* Highly Polished Visual Frame Component WITH STRICT HEIGHT FIX */}
                    <div className="w-full md:w-2/5 shrink-0 bg-[#f8fafc] p-2.5 border border-[#e2e8f0] rounded-sm shadow-sm">
                      <img
                        src={section.image_url}
                        alt={section.alt_text || section.section_title}
                        className="w-full h-auto max-h-56 object-cover filter grayscale-[15%] rounded-sm border border-[#e2e8f0]/40"
                      />
                      {section.alt_text && (
                        <p className="text-[10px] text-[#94a3b8] font-medium tracking-wide mt-2 text-center italic break-words">
                          {section.alt_text}
                        </p>
                      )}
                    </div>

                  </div>
                </div>
              ) : (
                // Safe Full Container Width Prose Fallback Block
                <div className="text-[13px] leading-relaxed text-[#475569] text-justify">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {section.paragraph_text}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 🏷️ FIXED BASELINE FOOTER ARCHIVE ATTESTATION */}
      <div className="mt-20 pt-6 border-t border-[#e2e8f0] flex justify-between items-center text-[9px] font-mono uppercase tracking-wider text-[#94a3b8]">
        <p>Aegis Data Node Pipeline v2.4</p>
        <p className="font-semibold text-[#64748b]">Internal Intelligence Record • Confidential</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 🎨 GLOBAL PREMIUM INLINE MARKDOWN INTERCEPT RENDERING COMPONENT REGISTRY
// INCLUDES STRICT BOUNDARY WRAPPING TO PREVENT PDF DISTORTION
// ---------------------------------------------------------------------------
const markdownComponents = {
  // SAAS BENTO GRID LIST CONVERSION
  ul: ({ node, ...props }) => (
    <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 my-6 p-0 list-none" {...props} />
  ),
  li: ({ node, ...props }) => (
    <li className="bg-[#f8fafc] border border-[#e2e8f0] p-4 rounded-sm text-[12px] font-medium text-[#334155] leading-normal relative pl-9 shadow-sm break-words" {...props}>
      <span className="absolute left-3.5 top-4.5 w-2 h-2 bg-[#2563eb] rounded-full" />
      {props.children}
    </li>
  ),
  // PREVENT CODE BLOCKS FROM BREAKING THE PAGE WIDTH
  pre: ({ node, ...props }) => (
    <pre className="bg-[#f1f5f9] p-3 rounded-sm my-4 overflow-hidden whitespace-pre-wrap break-words text-[10px] text-[#334155] border border-[#e2e8f0]" {...props} />
  ),
  code: ({ node, inline, ...props }) => (
    inline ? 
    <code className="bg-[#f1f5f9] px-1 py-0.5 rounded-sm text-[#2563eb] text-[11px] break-words" {...props} /> :
    <code className="break-words" {...props} />
  ),
  // HIGH-END STRIPED FINANCIAL DATA GRID CONVERSIONS WITH STRICT SIZING
  table: ({ node, ...props }) => (
    <div className="w-full my-8 border border-[#e2e8f0] rounded-sm overflow-hidden shadow-sm">
      <table className="min-w-full text-[11px] text-left border-collapse table-fixed" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => (
    <thead className="border-b border-[#cbd5e1] bg-[#f8fafc] text-[#0f172a] font-bold uppercase tracking-wider" {...props} />
  ),
  th: ({ node, ...props }) => (
    <th className="py-3.5 px-4 break-words" {...props} />
  ),
  td: ({ node, ...props }) => (
    <td className="py-3 px-4 border-b border-[#f1f5f9] text-[#475569] font-medium align-middle break-words" {...props} />
  ),
  tr: ({ node, ...props }) => (
    <tr className="hover:bg-[#f8fafc]/50 transition-colors odd:bg-white even:bg-[#f8fafc]/30" {...props} />
  ),
  // CLEAN INTERNAL TYPOGRAPHY PRIMITIVES
  h3: ({ node, ...props }) => (
    <h3 className="text-md font-bold text-[#0f172a] mt-6 mb-2 tracking-tight flex items-center gap-2 break-words" {...props} />
  ),
  h4: ({ node, ...props }) => (
    <h4 className="text-xs font-black text-[#64748b] uppercase tracking-widest mt-4 mb-1 break-words" {...props} />
  ),
  blockquote: ({ node, ...props }) => (
    <blockquote className="border-l-2 border-[#2563eb] pl-4 my-5 italic text-[#334155] bg-[#f0f4f8] py-2.5 pr-2 rounded-r-sm font-serif text-xs leading-relaxed break-words" {...props} />
  ),
  p: ({ node, ...props }) => <p className="my-3 leading-relaxed break-words" {...props} />
};