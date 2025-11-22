import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Profile, Recommendation

app = FastAPI(title="StyleSense AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "StyleSense AI backend is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# AI-like rules engine (deterministic heuristic to simulate AI suggestions)

def build_recommendations(profile: Profile) -> Recommendation:
    makeup: List[str] = []
    skincare: List[str] = []
    clothing: List[str] = []
    accessories: List[str] = []

    tone = (profile.skin_tone or "").lower()
    undertone = (profile.undertone or "").lower()

    # Makeup suggestions by undertone
    if undertone == "cool":
        makeup += [
            "Choose pink or berry blushes",
            "Opt for foundations with pink/neutral base",
            "Silver or cool-toned highlighter"
        ]
        accessories.append("Prefer silver, platinum, or white gold jewelry")
    elif undertone == "warm":
        makeup += [
            "Peach or coral blushes flatter warm undertones",
            "Golden highlighters and warm bronzers",
            "Foundations with yellow/golden base"
        ]
        accessories.append("Prefer gold or rose-gold jewelry")
    else:
        makeup += [
            "Neutral blush tones like rose",
            "Neutral foundation shades with balanced undertone"
        ]
        accessories.append("Mix of gold and silver works well")

    # Skincare suggestions by tone
    if tone in ["fair", "light"]:
        skincare += [
            "Daily SPF 50 and gentle cleansers",
            "Niacinamide for tone-evening",
        ]
    elif tone in ["medium", "tan"]:
        skincare += [
            "Daily SPF 30+, vitamin C serum",
            "Lightweight gel moisturizers"
        ]
    elif tone in ["deep", "dark"]:
        skincare += [
            "SPF 30 daily; look for no white-cast formulas",
            "Hydrating cleansers and ceramide moisturizers"
        ]

    # Clothing recommendations by body type
    btype = (profile.body_type or "").lower()
    if btype == "hourglass":
        clothing += [
            "Wrap dresses and high-waisted bottoms",
            "Tailored pieces that define the waist"
        ]
    elif btype == "pear":
        clothing += [
            "A-line skirts, statement tops to balance proportions",
            "Structured jackets and darker bottoms"
        ]
    elif btype == "rectangle":
        clothing += [
            "Peplum tops, belts, and layered textures",
            "High-rise pants and cropped jackets"
        ]
    elif btype == "inverted_triangle":
        clothing += [
            "V-necklines, A-line skirts, and straight-leg pants",
            "Avoid heavy shoulder padding"
        ]

    # Style preferences and occasions
    prefs = [p.lower() for p in (profile.style_preferences or [])]
    if "minimal" in prefs:
        clothing.append("Monochrome looks with clean lines and tailored fits")
    if "streetwear" in prefs:
        clothing.append("Relaxed silhouettes, sneakers, and graphic accents")
    if "classic" in prefs:
        clothing.append("Crisp shirts, trench coats, and neutral palettes")
    if "edgy" in prefs:
        clothing.append("Leather accents, metal details, and bold contrasts")
    if "boho" in prefs:
        clothing.append("Flowy fabrics, earthy tones, and layered accessories")

    # Accessories preferences
    if profile.accessories_pref:
        for a in profile.accessories_pref:
            accessories.append(f"Lean into {a} accessories as signature pieces")

    # Budget awareness
    if (profile.budget or "").lower() == "budget":
        accessories.append("Focus on versatile pieces and capsule wardrobe basics")
    elif (profile.budget or "").lower() == "premium":
        accessories.append("Invest in quality staples and timeless accessories")

    profile_summary = {
        "body_type": profile.body_type or "",
        "skin_tone": profile.skin_tone or "",
        "undertone": profile.undertone or "",
        "style_preferences": ", ".join(profile.style_preferences or []),
        "occasions": ", ".join(profile.occasions or []),
        "budget": profile.budget or ""
    }

    return Recommendation(
        profile_summary=profile_summary,
        makeup=makeup,
        skincare=skincare,
        clothing=clothing,
        accessories=accessories,
    )

class ProfileIn(BaseModel):
    name: Optional[str] = None
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    undertone: Optional[str] = None
    style_preferences: Optional[List[str]] = None
    occasions: Optional[List[str]] = None
    accessories_pref: Optional[List[str]] = None
    budget: Optional[str] = None

@app.post("/api/recommend", response_model=Recommendation)
def recommend(profile: ProfileIn):
    # Validate against Profile model and persist profile + recommendation
    profile_model = Profile(**profile.model_dump(exclude_none=True))

    # Build deterministic recommendations
    rec = build_recommendations(profile_model)

    # Persist documents if DB available
    try:
        if db is not None:
            create_document("profile", profile_model)
            create_document("recommendation", rec)
    except Exception as e:
        # Non-fatal storage error
        pass

    return rec

@app.get("/api/trends")
def trends():
    # Simple static trends to simulate AI + trends awareness
    return {
        "makeup": ["Soft Matte Lips", "Glazed Highlighter", "Monochrome Blush"],
        "skincare": ["Peptide Serums", "Ceramide Moisturizers", "SPF Tints"],
        "fashion": ["Relaxed Tailoring", "Quiet Luxury Basics", "Utility Cargo"],
        "accessories": ["Chunky Silver", "Micro Bags", "Sculptural Earrings"],
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
