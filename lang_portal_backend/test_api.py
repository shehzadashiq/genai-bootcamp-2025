import requests
import json

def test_conversion(text, description=""):
    url = "http://127.0.0.1:8080/api/listening/test-hindi-to-urdu"
    data = {"text": text}
    response = requests.post(url, json=data)
    print(f"\nTest: {description}")
    print(f"Input: {text}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}\n")
    print("-" * 80)

# Test cases
test_conversion(
    "कमज़ोर बिल्ली पर तरस आया उसने एक प्याले",
    "Original test case"
)

test_conversion(
    "मैं हिंदी में बात कर रहा हूं",
    "Present continuous tense"
)

test_conversion(
    "क्या आप मेरी मदद कर सकते हैं?",
    "Question with helping verb"
)

test_conversion(
    "१२३४५ रुपये में यह किताब मिलेगी",
    "Numbers and currency"
)

test_conversion(
    "आज सुबह का मौसम बहुत सुहावना है",
    "Weather and time expressions"
)

test_conversion(
    "वह पिछले पांच सालों से यहाँ रह रही है",
    "Complex past continuous with duration"
)

test_conversion(
    "बच्चे स्कूल में खेल रहे हैं और पढ़ रहे हैं",
    "Compound sentence with conjunction"
)

test_conversion(
    "माँ ने बच्चों के लिए खाना बनाया है",
    "Perfective aspect with postposition"
)

test_conversion(
    "अगर बारिश होगी तो मैं नहीं आऊँगा",
    "Conditional sentence"
)

test_conversion(
    "यह फिल्म बहुत अच्छी है, लेकिन थोड़ी लंबी है",
    "Contrastive conjunction"
)
