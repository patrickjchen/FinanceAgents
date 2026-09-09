"use client"; 
import React, { useState } from 'react';

const QueryInputBox: React.FC<{ onSubmit: (query: string) => void }> = ({ onSubmit }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full max-w-2xl mx-auto my-6">
      <input
        className="flex-1 px-4 py-2 border rounded text-base bg-[var(--color-background)] text-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
        type="text"
        placeholder="Please enter your question..."
        value={input}
        onChange={e => setInput(e.target.value)}
      />
      <button
        type="submit"
        className="px-4 py-2 rounded bg-[var(--color-primary)] text-white font-medium hover:opacity-90 transition"
      >
        Submit
      </button>
    </form>
  );
};

export default QueryInputBox; 