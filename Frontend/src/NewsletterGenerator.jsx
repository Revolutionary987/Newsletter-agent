import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export default function NewsletterGenerator() {
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('');
  const [tone, setTone] = useState('');
  const [length, setLength] = useState('');
  const [keyPoints, setKeyPoints] = useState('');
  const [instructions, setInstructions] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    
    // Simulating generation delay for UI demonstration
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#F9F9F6] text-slate-900 font-sans p-6 md:p-12 flex flex-col items-center justify-center">
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;600;700&display=swap');
        .font-serif { font-family: 'Playfair Display', serif; }
        .font-sans { font-family: 'Inter', sans-serif; }
      `}} />

      <div className="w-full max-w-3xl">
        {/* Header Section */}
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

        {/* Form Container */}
        <div className="bg-white rounded-sm border border-slate-200/60 shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] p-8 md:p-12">
          <form onSubmit={handleSubmit} className="space-y-10">
            
            {/* Topic Field */}
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

            {/* Dropdowns Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-2 relative">
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
                    <option value="public">General Public</option>
                    <option value="tech">Tech Enthusiasts</option>
                    <option value="executives">Executives</option>
                    <option value="students">Students</option>
                  </select>
                  <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="space-y-2 relative">
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
                    <option value="professional">Professional & Objective</option>
                    <option value="inspiring">Inspiring</option>
                    <option value="conversational">Conversational</option>
                    <option value="analytical">Analytical</option>
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
                  { id: 'short', label: 'Short', desc: '300-500 words' },
                  { id: 'medium', label: 'Medium', desc: '500-1000 words' },
                  { id: 'long', label: 'Long', desc: '1000-1500 words' },
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

            {/* Key Points Textarea */}
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
              ></textarea>
            </div>

            {/* Additional Instructions */}
            <div className="space-y-2">
              <label className="block text-[10px] md:text-xs uppercase tracking-widest text-slate-500 font-semibold">
                Additional Instructions <span className="text-slate-400 font-normal normal-case tracking-normal ml-1">(Optional)</span>
              </label>
              <textarea 
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Any specific sources, quotes, or stylistic requests?"
                rows={3}
                className="w-full bg-transparent border border-gray-300 p-4 text-slate-800 placeholder:text-slate-300 focus:outline-none focus:border-slate-900 transition-colors rounded-sm resize-none"
              ></textarea>
            </div>

            {/* Submit Button */}
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
      </div>
    </div>
  );
}
