"""
Example: Complete user journey with WOW features
Demonstrates the full flow: Calculate → Get FAQ → Explain Terms
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:5000"


def complete_user_journey():
    """Simulate a complete user journey through the pension calculator"""
    
    print("\n" + "🎬" * 40)
    print("COMPLETE USER JOURNEY - Anna's Pension Planning Story")
    print("🎬" * 40 + "\n")
    
    # ========================================
    # STEP 1: User Data Input
    # ========================================
    print("📝 STEP 1: Anna enters her data")
    print("-" * 70)
    
    user_data = {
        "age": 35,
        "gender": "female",
        "gross_salary": 8000.0,
        "work_start_year": 2010,
        "work_end_year": 2050,
        "industry": "IT",
        "position": "Senior Developer",
        "company": "TechCorp Poland",
        "sick_leave_days_per_year": 5
    }
    
    print(f"👤 Name: Anna")
    print(f"👶 Age: {user_data['age']} years old")
    print(f"💼 Job: {user_data['position']} in {user_data['industry']}")
    print(f"💰 Salary: {user_data['gross_salary']:,} PLN gross/month")
    print(f"📅 Working since: {user_data['work_start_year']}")
    print(f"🏖️  Plans to retire: {user_data['work_end_year']}")
    print()
    
    # ========================================
    # STEP 2: Calculate Pension
    # ========================================
    print("🧮 STEP 2: Calculating Anna's pension...")
    print("-" * 70)
    
    calc_payload = {
        "user_data": user_data
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/calculate_pension_local", json=calc_payload)
        
        if response.status_code == 200:
            calc_result = response.json()
            monthly_pension = calc_result.get("monthly_pension", 0)
            replacement_rate = calc_result.get("details", {}).get("pension_metrics", {}).get("replacement_rate_percent", 0)
            years_to_work_longer = calc_result.get("details", {}).get("pension_metrics", {}).get("years_to_work_longer")
            
            print(f"✅ Calculation complete!\n")
            print(f"💵 Monthly pension: {monthly_pension:,.2f} PLN")
            print(f"📊 Replacement rate: {replacement_rate:.1f}%")
            
            if years_to_work_longer and years_to_work_longer > 0:
                print(f"⚠️  Recommendation: Work {years_to_work_longer} more years to reach 60% replacement rate")
            
            print()
            
        else:
            print(f"❌ Calculation failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # ========================================
    # STEP 3: Generate Personalized FAQ
    # ========================================
    print("💬 STEP 3: Generating personalized FAQ for Anna...")
    print("-" * 70)
    print("Anna sees these questions automatically:\n")
    
    faq_payload = {
        "user_data": user_data,
        "calculation_result": {
            "monthly_pension": monthly_pension,
            "replacement_rate": replacement_rate,
            "years_to_work_longer": years_to_work_longer
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/faq", json=faq_payload)
        
        if response.status_code == 200:
            faq_result = response.json()
            faq_items = faq_result.get("faq", [])
            
            # Show top 3 most relevant questions
            for i, item in enumerate(faq_items[:3], 1):
                relevance_emoji = "🔴" if item.get("relevance") == "high" else "🟡" if item.get("relevance") == "medium" else "🟢"
                print(f"{relevance_emoji} Question {i}: {item.get('question')}")
                print(f"   💡 {item.get('answer')[:150]}...")
                print()
            
            print(f"[... and {len(faq_items) - 3} more questions]\n")
            
        else:
            print(f"⚠️  FAQ generation skipped (requires AI)\n")
            
    except Exception as e:
        print(f"⚠️  FAQ generation failed (AI not available): {e}\n")
    
    # ========================================
    # STEP 4: Anna Clicks on a Complex Term
    # ========================================
    print("🤔 STEP 4: Anna doesn't understand 'waloryzacja'...")
    print("-" * 70)
    print("She clicks on the term to get an explanation:\n")
    
    terms_payload = {
        "terms": ["waloryzacja"],
        "user_data": user_data,
        "calculation_result": {
            "monthly_pension": monthly_pension,
            "replacement_rate": replacement_rate
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/explain_terms", json=terms_payload)
        
        if response.status_code == 200:
            terms_result = response.json()
            explanations = terms_result.get("explanations", [])
            
            if explanations:
                expl = explanations[0]
                print(f"📚 Term: {expl.get('term').upper()}")
                print(f"\n💡 Simple explanation:")
                print(f"   {expl.get('simple_explanation')}")
                print(f"\n🎯 Example for Anna:")
                print(f"   {expl.get('example')}")
                print()
                
                related = expl.get('related_terms', [])
                if related:
                    print(f"🔗 Related terms Anna might want to learn: {', '.join(related)}")
                    print()
            
        else:
            print(f"⚠️  Terms explanation skipped (requires AI)\n")
            
    except Exception as e:
        print(f"⚠️  Terms explanation failed (AI not available): {e}\n")
    
    # ========================================
    # STEP 5: Anna Explores More
    # ========================================
    print("🔍 STEP 5: Anna wants to learn more...")
    print("-" * 70)
    print("She asks the system to explain more complex terms:\n")
    
    more_terms_payload = {
        "terms": [
            "kapitał początkowy",
            "współczynnik zastąpienia",
            "średnie dalsze trwanie życia"
        ],
        "user_data": user_data
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/explain_terms", json=more_terms_payload)
        
        if response.status_code == 200:
            terms_result = response.json()
            explanations = terms_result.get("explanations", [])
            
            for expl in explanations:
                print(f"📖 {expl.get('term')}")
                print(f"   → {expl.get('simple_explanation')[:100]}...")
                print()
            
        else:
            print(f"⚠️  Additional terms skipped (requires AI)\n")
            
    except Exception as e:
        print(f"⚠️  Additional terms failed (AI not available): {e}\n")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print("=" * 70)
    print("✨ JOURNEY COMPLETE!")
    print("=" * 70)
    print()
    print("What Anna learned:")
    print(f"  ✅ Her pension: {monthly_pension:,.2f} PLN ({replacement_rate:.1f}% of salary)")
    print(f"  ✅ What this means: She'll get {replacement_rate:.1f}% of her last salary")
    print(f"  ✅ What she can do: Work {years_to_work_longer} more years for better pension" if years_to_work_longer else "  ✅ Her pension is on track!")
    print(f"  ✅ Understanding: Learned what waloryzacja, kapitał, and other terms mean")
    print(f"  ✅ Confidence: Can now make informed decisions about her retirement")
    print()
    print("🎯 Anna went from confused → informed → empowered!")
    print()


def showcase_wow_features_separately():
    """Show each WOW feature individually for demo purposes"""
    
    print("\n" + "🌟" * 40)
    print("WOW FEATURES SHOWCASE")
    print("🌟" * 40 + "\n")
    
    # Sample user with calculated pension
    user_data = {
        "age": 40,
        "gender": "male",
        "gross_salary": 12000.0,
        "industry": "Finance",
        "position": "Manager"
    }
    
    calc_result = {
        "monthly_pension": 5800.0,
        "replacement_rate": 48.3,
        "years_to_work_longer": 3
    }
    
    print("👤 Demo User: 40-year-old Finance Manager, 12,000 PLN salary")
    print(f"💵 Calculated pension: {calc_result['monthly_pension']:,.2f} PLN\n")
    
    # ========================================
    # WOW Feature #1: FAQ
    # ========================================
    print("🎯 WOW FEATURE #1: AI-Generated FAQ")
    print("-" * 70)
    
    faq_payload = {
        "user_data": user_data,
        "calculation_result": calc_result
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/faq", json=faq_payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✨ Generated {len(result.get('faq', []))} personalized questions:\n")
            
            for i, item in enumerate(result.get("faq", [])[:3], 1):
                print(f"{i}. {item.get('question')}")
            
            print("\n[Frontend would show these in expandable accordion]\n")
        else:
            print("⚠️  Requires Perplexity API\n")
    except:
        print("⚠️  API not available or AI not configured\n")
    
    # ========================================
    # WOW Feature #2: Terms
    # ========================================
    print("📚 WOW FEATURE #2: Smart Terms Explainer")
    print("-" * 70)
    
    terms_payload = {
        "terms": ["OFE", "emerytura pomostowa"],
        "user_data": user_data
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/explain_terms", json=terms_payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✨ Explained {len(result.get('explanations', []))} terms:\n")
            
            for expl in result.get("explanations", []):
                print(f"📖 {expl.get('term')}")
                print(f"   💡 {expl.get('simple_explanation')[:80]}...")
                print()
            
            print("[Frontend would show these in tooltips/modals]\n")
        else:
            print("⚠️  Requires Perplexity API\n")
    except:
        print("⚠️  API not available or AI not configured\n")


if __name__ == "__main__":
    print("\nChoose demo:")
    print("1. Complete user journey (Anna's story)")
    print("2. WOW features showcase")
    print()
    
    choice = input("Enter 1 or 2 (or press Enter for both): ").strip()
    
    if choice == "1" or choice == "":
        complete_user_journey()
    
    if choice == "2" or choice == "":
        showcase_wow_features_separately()
    
    print("\n" + "🎉" * 40)
    print("Demo complete! These features make pension planning engaging!")
    print("🎉" * 40 + "\n")
