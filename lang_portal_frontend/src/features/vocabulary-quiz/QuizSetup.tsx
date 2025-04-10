import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  FormControl,
  FormLabel,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Heading,
} from '@chakra-ui/react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { vocabularyQuizApi } from './api';
import { groupsApi } from '@/services/api';
import { QuizConfig, QuizDifficulty } from './types';
import { AxiosResponse } from 'axios';

// Define the Group interface
interface Group {
  id: number;
  name: string;
  word_count: number;
}

export const QuizSetup: React.FC = () => {
  const navigate = useNavigate();
  const [config, setConfig] = React.useState<QuizConfig>({
    groupId: 0,
    difficulty: 'easy',
    wordCount: 10,
  });

  // Fetch groups with the merge_by_difficulty parameter set to true
  const { data: groups = [], isLoading: isLoadingGroups } = useQuery({
    queryKey: ['groups', 'merged'],
    queryFn: () => groupsApi.getAll(1, true).then((res) => res.data.items as Group[])
  });

  const startQuiz = useMutation({
    mutationFn: (config: QuizConfig) => vocabularyQuizApi.startQuiz(config.groupId, config.wordCount, config.difficulty),
    onSuccess: (response: AxiosResponse<any>) => {
      navigate(`/apps/vocabulary-quiz/session`, {
        state: { session: response }
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startQuiz.mutate(config);
  };

  return (
    <Card p={6} maxW="xl" mx="auto" mt={8}>
      <Heading size="lg" mb={6}>Vocabulary Quiz Setup</Heading>
      
      <form onSubmit={handleSubmit}>
        <FormControl mb={4}>
          <FormLabel>Word Group</FormLabel>
          <Select
            value={config.groupId}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setConfig({ ...config, groupId: parseInt(e.target.value) })}
            placeholder="Select a word group"
            isDisabled={isLoadingGroups}
          >
            {groups.map((group: Group) => (
              <option key={group.id} value={group.id}>
                {group.name} ({group.word_count} words)
              </option>
            ))}
          </Select>
        </FormControl>

        <FormControl mb={4}>
          <FormLabel>Difficulty</FormLabel>
          <Select
            value={config.difficulty}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => 
              setConfig({ ...config, difficulty: e.target.value as QuizDifficulty })}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>
        </FormControl>

        <FormControl mb={6}>
          <FormLabel>Number of Words</FormLabel>
          <NumberInput
            value={config.wordCount}
            onChange={(_: string, value: number) => setConfig({ ...config, wordCount: value })}
            min={5}
            max={20}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <Button
          type="submit"
          colorScheme="blue"
          isLoading={startQuiz.isPending || isLoadingGroups}
          isDisabled={!config.groupId}
          w="full"
        >
          Start Quiz
        </Button>
      </form>
    </Card>
  );
};
