from app.services.llm_router import map_google_model

def test_map_google_model():
    # 1. Test fictitious 3.5-flash mapping (case-insensitive checks)
    assert map_google_model("gemini-3.5-flash") == "gemini-3.5-flash,gemini-2.5-flash,gemini-1.5-flash"
    assert map_google_model("GEMINI-3.5-FLASH") == "GEMINI-3.5-FLASH,gemini-3.5-flash,gemini-2.5-flash,gemini-1.5-flash"
    
    # 2. Test fictitious 3.1-pro mapping
    assert map_google_model("gemini-3.1-pro-preview") == "gemini-3.1-pro-preview,gemini-2.5-pro,gemini-1.5-pro"
    assert map_google_model("gemini-3.1-pro") == "gemini-3.1-pro,gemini-2.5-pro,gemini-1.5-pro"
    
    # 3. Test other fictitious naming variations
    assert map_google_model("gemini-3-flash") == "gemini-3-flash,gemini-3.5-flash,gemini-2.5-flash,gemini-1.5-flash"
    assert map_google_model("gemini-3-pro") == "gemini-3-pro,gemini-2.5-pro,gemini-1.5-pro"
    
    # 4. Test that placeholder 2.5 models map to actual stable models
    assert map_google_model("gemini-2.5-flash") == "gemini-2.5-flash,gemini-3.5-flash,gemini-1.5-flash"
    assert map_google_model("gemini-1.5-pro") == "gemini-1.5-pro"
    
    # 5. Test retired 2.0-flash mapping
    assert map_google_model("gemini-2.0-flash") == "gemini-2.5-flash,gemini-3.5-flash,gemini-1.5-flash"
    
    # 6. Test empty or None values
    assert map_google_model("") == ""
    assert map_google_model(None) == ""

if __name__ == "__main__":
    test_map_google_model()
    print("All model mapping assertions passed!")
