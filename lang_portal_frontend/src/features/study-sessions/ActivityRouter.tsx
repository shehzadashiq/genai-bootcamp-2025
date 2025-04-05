import React from 'react';
import { VocabularyQuiz } from '../vocabulary-quiz/VocabularyQuiz';
import { Flashcards } from '../flashcards';
import { StudySessionResponse } from '@/types';

interface ActivityRouterProps {
  session: StudySessionResponse;
  quizSessionId?: string;
}

export const ActivityRouter: React.FC<ActivityRouterProps> = ({ session, quizSessionId }) => {
  // Map activity names to their corresponding components
  const activityMap: Record<string, React.FC<{ sessionId: string }>> = {
    'Vocabulary Quiz': VocabularyQuiz,
    'Flashcards': Flashcards,
  };

  const ActivityComponent = session.activity_name ? activityMap[session.activity_name] : null;

  if (!ActivityComponent) {
    return (
      <div className="text-center p-4">
        <p className="text-lg text-gray-600">
          Unknown activity type: {session.activity_name || 'No activity name provided'}
        </p>
      </div>
    );
  }

  // Use the quiz session ID if available, otherwise fall back to the regular session ID
  const sessionIdToUse = quizSessionId || session.id.toString();
  return <ActivityComponent sessionId={sessionIdToUse} />;
};
