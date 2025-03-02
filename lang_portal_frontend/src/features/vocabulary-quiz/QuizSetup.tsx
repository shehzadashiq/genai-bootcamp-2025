import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
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
import { groupsApi } from '../groups/api';
import { QuizConfig } from './types';

export const QuizSetup: React.FC = () => {
  const navigate = useNavigate();
  const [config, setConfig] = React.useState<QuizConfig>({
    groupId: 0,
    difficulty: 'easy',
    wordCount: 10,
  });

  const { data: groups = [] } = useQuery(['groups'], () =>
    groupsApi.listGroups().then((res) => res.items)
  );

  const startQuiz = useMutation(vocabularyQuizApi.startQuiz, {
    onSuccess: (data) => {
      navigate(`/vocabulary-quiz/${data.session_id}`);
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
            onChange={(e) => setConfig({ ...config, groupId: parseInt(e.target.value) })}
            placeholder="Select a word group"
          >
            {groups.map((group) => (
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
            onChange={(e) => setConfig({ ...config, difficulty: e.target.value })}
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
            onChange={(_, value) => setConfig({ ...config, wordCount: value })}
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
          isLoading={startQuiz.isLoading}
          isDisabled={!config.groupId}
          w="full"
        >
          Start Quiz
        </Button>
      </form>
    </Card>
  );
};
