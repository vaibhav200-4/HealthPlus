import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.api.hospitals import get_all_hospitals
from app.schemas.hospital_schema import HospitalBase

def test_get_all_hospitals():
    print("==========================================")
    print("TEST: GET /api/hospitals Response Validation")
    print("==========================================")
    
    hospitals = get_all_hospitals()
    print(f"Retrieved {len(hospitals)} hospital records.")
    
    for idx, h in enumerate(hospitals):
        # Verify it conforms to HospitalBase
        parsed = HospitalBase.model_validate(h)
        assert isinstance(parsed.departments, list), f"Hospital {parsed.id} departments is not a list!"
        if idx < 5:
            print(f"Hospital [{parsed.id}] '{parsed.hospital_name}' -> departments: {parsed.departments}")

    print("==========================================")
    print("GET /api/hospitals TEST PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_get_all_hospitals()
