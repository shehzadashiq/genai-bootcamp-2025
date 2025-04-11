import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8080/api"

def test_merged_groups():
    """Test the merged groups functionality"""
    print("Testing merged groups API...")
    
    # Get regular groups
    response = requests.get(f"{BASE_URL}/groups")
    regular_groups = response.json()
    print(f"Regular groups count: {len(regular_groups['items'])}")
    
    # Get merged groups
    response = requests.get(f"{BASE_URL}/groups?merge_by_difficulty=true")
    merged_groups = response.json()
    print(f"Merged groups count: {len(merged_groups['items'])}")
    
    # Print the merged groups
    print("\nMerged groups:")
    for group in merged_groups['items']:
        print(f"- {group['name']} ({group['word_count']} words)")
    
    return merged_groups

def test_start_quiz_with_merged_group(group_id):
    """Test starting a quiz with a merged group"""
    print(f"\nTesting quiz start with merged group ID: {group_id}")
    
    # Start a quiz with the merged group
    payload = {
        "group_id": group_id,
        "word_count": 5,
        "difficulty": "easy"
    }
    
    response = requests.post(f"{BASE_URL}/vocabulary-quiz/start/", json=payload)
    quiz_data = response.json()
    
    if 'error' in quiz_data:
        print(f"Error: {quiz_data['error']}")
        return None
    
    print(f"Quiz started with session ID: {quiz_data['session_id']}")
    print(f"Number of words in quiz: {len(quiz_data['words'])}")
    
    # Print the first word as an example
    if quiz_data['words']:
        first_word = quiz_data['words'][0]
        print("\nExample word:")
        print(f"Word: {first_word['word']['urdu']} ({first_word['word']['english']})")
        print(f"Options: {first_word['options']}")
    
    return quiz_data

if __name__ == "__main__":
    # Test merged groups
    merged_groups = test_merged_groups()
    
    # If we have merged groups, test starting a quiz with the first one
    if merged_groups and merged_groups['items']:
        first_group_id = merged_groups['items'][0]['id']
        test_start_quiz_with_merged_group(first_group_id)
