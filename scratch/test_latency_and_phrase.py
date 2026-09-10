import sys
import time

sys.path.insert(0, r"c:\Users\HP\OneDrive\Desktop\one-tab-project\HealthPlus")
sys.path.insert(0, r"c:\Users\HP\OneDrive\Desktop\one-tab-project\HealthPlus\ai_voice_agent")

from processor.hospital_handler import HospitalHandler

handler = HospitalHandler()
res1 = handler._handle_nearby_search(intent_data={}, user_text="Show hospitals near me")
print("Prompt response:", res1)

t0 = time.time()
res = handler._handle_nearby_search(intent_data={"location": "Mumbai"}, user_text="Mumbai")
t1 = time.time()

print(f"\nResponse Time: {t1 - t0:.3f}s")
print(f"Response Output:\n{res}\n")

# Second call to test 0ms caching latency
t2 = time.time()
res2 = handler._handle_nearby_search(intent_data={"location": "Mumbai"}, user_text="Mumbai")
t3 = time.time()
print(f"Cached Response Time: {t3 - t2:.3f}s")

if "The top five nearest are:" in res:
    print("\n✅ TEST PASSED: 'The top five nearest are:' present in response!")
else:
    print("\n❌ TEST FAILED: phrase missing!")
