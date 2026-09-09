"use client"; 
import React, { useState, useEffect } from 'react';

const NavigationTopBar: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <nav className="w-full flex items-center justify-between px-6 py-3 border-b bg-[var(--color-background)]">
      <div className="text-xl font-bold text-[var(--color-primary)]">bankerAI</div>
      <button
        className="rounded px-3 py-1 border text-sm text-[var(--color-primary)] border-[var(--color-primary)] hover:bg-[var(--color-primary)] hover:text-white transition"
        onClick={() => setIsDark((d) => !d)}
        aria-label="Toggle Theme"
      >
        {isDark ? ' Dark Mode' : ' Light Mode'}
      </button>
    </nav>
  );
};

export default NavigationTopBar;