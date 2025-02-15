import React from 'react';
import { VocabularyQuiz } from '../vocabulary-quiz/VocabularyQuiz';
import { StudySessionResponse } from '@/types';

interface ActivityRouterProps {
  session: StudySessionResponse;
}

export const ActivityRouter: React.FC<ActivityRouterProps> = ({ session }) => {
  // Map activity names to their corresponding components
  const activityMap: Record<string, React.FC<{ sessionId: string }>> = {
    'Vocabulary Quiz': VocabularyQuiz,
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

  return <ActivityComponent sessionId={session.id.toString()} />;
};
