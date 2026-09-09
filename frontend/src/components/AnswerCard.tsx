"use client";
import React, { useState } from 'react';

interface AnswerCardProps {
  answer: string;
  details?: string;
}

const AnswerCard: React.FC<AnswerCardProps> = ({ answer, details }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="w-full max-w-2xl mx-auto bg-white dark:bg-[var(--color-background)] border rounded shadow p-6 my-4">
      <div className="text-base text-gray-900 dark:text-gray-100 mb-2">{answer}</div>
      {details && (
        <>
          <button
            className="text-sm text-[var(--color-primary)] underline mb-2"
            onClick={() => setShowDetails(d => !d)}
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
          {showDetails && (
            <div className="mt-2 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line border-t pt-2">{details}</div>
          )}
        </>
      )}
    </div>
  );
};

export default AnswerCard;