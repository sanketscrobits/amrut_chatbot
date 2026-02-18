"""
SQL Template Caching System
Provides fast SQL generation for common query patterns.
"""

import re
from typing import Dict, Optional

# EXPANDED: Template definitions (5 → 15+ templates)
SQL_TEMPLATES = {
    # Original templates
    "list_all_places": """
        SELECT name_en, name_mr, description_en, address, lat, lng, image_url
        FROM tourist_places
        LIMIT {limit};
    """,
    
    "places_in_district": """
        SELECT tp.name_en, tp.name_mr, tp.description_en, tp.address, tp.lat, tp.lng, tp.image_url
        FROM tourist_places AS tp
        JOIN districts AS d ON tp.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%'
        LIMIT {limit};
    """,
    
    "count_all_places": """
        SELECT COUNT(*) FROM tourist_places;
    """,
    
    "count_districts": """
        SELECT COUNT(*) FROM districts;
    """,
    
    "top_n_places": """
        SELECT name_en, name_mr, description_en, address, image_url
        FROM tourist_places
        LIMIT {limit};
    """,
    
    # NEW: District queries
    "list_all_districts": """
        SELECT name_en, name_mr, lat, lng
        FROM districts
        ORDER BY name_en
        LIMIT {limit};
    """,
    
    "district_by_name": """
        SELECT id, name_en, name_mr, lat, lng
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    
    # NEW: Filtered place queries
    "places_with_description": """
        SELECT name_en, name_mr, description_en, address, image_url
        FROM tourist_places
        WHERE description_en IS NOT NULL AND description_en != ''
        LIMIT {limit};
    """,
    
    "places_with_images": """
        SELECT name_en, description_en, address, image_url
        FROM tourist_places
        WHERE image_url IS NOT NULL AND image_url != ''
        LIMIT {limit};
    """,
    
    # NEW: Count queries
    "count_places_in_district": """
        SELECT COUNT(*) as count
        FROM tourist_places tp
        JOIN districts d ON tp.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%';
    """,
    
    # NEW: Analytics queries
    "district_with_most_places": """
        SELECT d.name_en, d.name_mr, COUNT(tp.id) as place_count
        FROM districts d
        LEFT JOIN tourist_places tp ON d.id = tp.district_id
        GROUP BY d.id, d.name_en, d.name_mr
        ORDER BY place_count DESC
        LIMIT 1;
    """,
    
    "districts_with_places": """
        SELECT d.name_en, d.name_mr, COUNT(tp.id) as place_count
        FROM districts d
        INNER JOIN tourist_places tp ON d.id = tp.district_id
        GROUP BY d.id, d.name_en, d.name_mr
        HAVING COUNT(tp.id) > 0
        ORDER BY place_count DESC;
    """,
    
    # NEW: Business queries
    "count_all_businesses": """
        SELECT COUNT(*) FROM local_businesses;
    """,
    
    "list_all_businesses": """
        SELECT name_en, description_en, address
        FROM local_businesses
        LIMIT {limit};
    """,

    # NEW: Detailed Templates for CSV Analysis
    "get_district_population": """
        SELECT name_en, population
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    "get_best_time_visit_district": """
        SELECT name_en, best_time_to_visit_en
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    "get_place_entry_fee": """
        SELECT name_en, entry_fee
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "get_place_hours": """
        SELECT name_en, opening_hours_en
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "get_place_description": """
        SELECT name_en, description_en
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "list_services_in_district": """
        SELECT es.name, es.phone, es.address, es.available_24_7
        FROM emergency_services es
        JOIN districts d ON es.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%' AND es.service_type ILIKE '%{service_type}%'
        LIMIT 10;
    """,
    "get_service_contact": """
        SELECT name, phone, address
        FROM emergency_services
        WHERE name ILIKE '%{name}%'
        LIMIT 1;
    """,
    "list_businesses_in_district": """
        SELECT b.name_en, b.description_en, b.address, b.phone
        FROM local_businesses b
        JOIN districts d ON b.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%'
             AND (b.name_en ILIKE '%{category}%' OR b.description_en ILIKE '%{category}%')
        LIMIT 10;
    """,
    "get_business_contact": """
        SELECT name_en, phone, email, address
        FROM local_businesses
        WHERE name_en ILIKE '%{name}%'
        LIMIT 1;
    """,
    "get_district_description": """
        SELECT name_en, name_mr, description_en, tourist_highlights_en
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
}

# Demo Script Categories and Examples
# This section is for documentation purposes, illustrating the capabilities of the SQL Agent.

## 1. SQL Agent (Factual & Structured Data)
# *Showcases the fixed schema pruning, joining, and expanded template matching.*

# | Category | Query | Expected Outcome |
# | :--- | :--- | :--- |
# | **Statistics** | "How many districts are in Maharashtra?" | **36** (Shows precise counting) |
# | **Demographics** | "What is the population of Solapur?" | **1.4 Million** (Shows factual retrieval) |
# | **District Comparisons** | "Which district has the highest population?" | **Washim** (Shows aggregation/ordering) |
# | **Tourism** | "Tell me about Pune district" | **Pune District Info** (Shows complex description retrieval) |
# | **Local Attractions** | "Show me tourist places in Kolhapur" | **List of Places** (Shows SQL JOIN functionality) |
# | **Specific Categories** | "List all forts in Maharashtra" | **Historical Forts** (Shows category filtering) |
# | **Details** | "What is the entry fee for Aga Khan Palace?" | **₹25 / ₹300** (Shows specific attribute lookup) |
# | **Timing** | "When is the best time to visit Nagpur?" | **Winter (Oct to Feb)** (Shows column-specific retrieval) |

## 2. Emergency Services & Businesses
# *Showcases the local search and connection between entities.*

# | Category | Query | Expected Outcome |
# | :--- | :--- | :--- |
# | **Emergency** | "List hospitals in Pune" | **Ruby Hall, Sancheti, etc.** (Shows service filtering) |
# | **Police** | "Find police stations in Nashik" | **List of Stations** (Shows service type filtering) |
# | **Convenience** | "Are there any public toilets in Mumbai?" | **List of Toilets** (Shows niche service lookup) |
# | **Services** | "Are there any taxi services in Pune?" | **Pune Taxi Service** (Shows business description matching) |
# | **Local Professional Services** | "Find a tourism guide for forts" | **Rahul Tourism Guide** (Shows skill-based business lookup) |
# | **Hospitality** | "Suggest some homestays or hotels in Pune" | **Sahyadri Homestay, etc.** (Shows multi-line rich responses) |

# Helper to assist with singularization
def singularize(word):
    """
    Very basic singularization for our specific domain keywords.
    """
    word = word.strip("?.! ").lower() # Strip punctuation and lowercase
    
    # Custom mappings based on DB inspection
    mappings = {
        "hospitals": "Hospital",
        "hospital": "Hospital",
        "pharmacies": "Pharmacy",
        "pharmacy": "Pharmacy",
        "police stations": "Police",  # DB has 'Police'
        "police station": "Police",
        "police": "Police",
        "public toilets": "Public Toilet",
        "public toilet": "Public Toilet",
        "hotels": "Hotel",
        "hotel": "Hotel",
        "restaurants": "Restaurant",
        "restaurant": "Restaurant",
        "taxis": "Taxi",
        "taxi": "Taxi"
    }
    
    if word in mappings:
        return mappings[word]
        
    # Default stripping 's' if not found (basic fallback)
    if word.endswith('s') and word[:-1] in mappings.values(): # e.g. Forts -> Fort (if we had Fort)
         pass # Logic here is tricky without full dictionary. 
    
    # For now, just return title case if not in mapping, or strip 's' if it looks like a simple plural
    if word.endswith('s'):
        return word[:-1].title()
        
    return word.title()


# EXPANDED: Pattern matchers (6 → 20+ patterns)
QUERY_PATTERNS = [
    # --- HIGH PRIORITY: SPECIFIC ENTITIES ---
    {
        "pattern": r"(?:entry fee|ticket|cost|price).*(?:for|of)\s+([a-zA-Z\s]+)",
        "template": "get_place_entry_fee",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:opening hours|timing|when does it open|open hours).*(?:of|for)\s+([a-zA-Z\s]+)",
        "template": "get_place_hours", 
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|describe|info on|details of|what is)\s+([a-zA-Z\s]+?)\s+(?:fort|temple|museum|place|monument|attraction|palace|cave|garden|park|dam|lake)",
        "template": "get_place_description",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|describe|info on|details of|what is)\s+([a-zA-Z\s]+?)(?:\s+district|\s+city|\s+location)",
        "template": "get_district_description",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|describe|info on|details of|what is|i want to know about|what about)\s+([a-zA-Z\s]+)",
        "template": "get_district_description",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    
    # --- MEDIUM PRIORITY: ATTRIBUTES & COUNTS ---
    {
        "pattern": r"(?:what is the\s+)?population of ([a-zA-Z\s]+)",
        "template": "get_district_population",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    
    # Original patterns
    {
        "pattern": r"(?:show|list|give|find|get|display).+(?:all|every).+(?:tourist place|attraction|monument|heritage|site|sightseeing|spot|destination)",
        "template": "list_all_places",
        "params": {"limit": 10}
    },
    {
        "pattern": r"(?:tourist place|famous (?:spot|place)|attraction|thing(?:s)? to (?:see|do|visit)|place(?:s)? to (?:visit|see|explore)|worth visiting|must see|point(?:s)? of interest|popular place|best place|top place|spot).+(?:in|near|at|around|of)\s+(\w+)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"(?:in|near|at|around).+?(\w+).+(?:tourist place|famous (?:spot|place)|attraction|thing(?:s)? to (?:see|do)|place(?:s)? to visit|spot)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"(?:what are|what's|suggest|recommend).+(?:famous|popular|best|top|interesting).+(?:in|near|at|around|of)\s+(\w+)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"(?:how many|count|total|number).+(?:tourist place|attraction|monument|place|site)",
        "template": "count_all_places",
        "params": {}
    },
    {
        "pattern": r"how many.+district",
        "template": "count_districts",
        "params": {}
    },
    {
        "pattern": r"(?:top|first)\s+(\d+).+tourist place",
        "template": "top_n_places",
        "extractor": lambda m: {"limit": int(m.group(1))}
    },
    
    # NEW: District query patterns
    {
        "pattern": r"(?:show|list|give).+(?:all|every).+districts?",
        "template": "list_all_districts",
        "params": {"limit": 36}
    },
    {
        "pattern": r"(?:show|find|get).+district.+(?:named?|called)\s+(\w+)",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:info|information|details?|tell me about|what is).+district.+(\w+)",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:info|information|details?|tell me about|what is).+(\w+).+district",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    
    # NEW: Filtered place patterns
    {
        "pattern": r"(?:show|list|find|get|suggest|recommend).*(?:forts?|monuments?|temples?|museums?|places?|spots?|destinations?|attractions?).+(?:in|at|of|near|around)\s+(\w+)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"places?.+(?:with|having|contains?).+(?:description|detail|info)",
        "template": "places_with_description",
        "params": {"limit": 10}
    },
    {
        "pattern": r"places?.+(?:with|having).+(?:image|photo|picture)",
        "template": "places_with_images",
        "params": {"limit": 10}
    },
    
    # NEW: Count patterns
    {
        "pattern": r"how many.+places?.+(?:in|at|near)\s+(\w+)",
        "template": "count_places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"count.+places?.+(?:in|at)\s+(\w+)",
        "template": "count_places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },

    # NEW: Detailed Templates for CSV Analysis (Population, Best Time, Etc)
    {
        "pattern": r"(?:how many people|population).+(?:in|at|of)\s+([a-zA-Z]+)",
        "template": "get_district_population",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"best time to visit (.+)",
        "template": "get_best_time_visit_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:when should I (?:visit|go to|plan|travel)|best (?:month|season|time) (?:to visit|for)|ideal time (?:to visit|for)|when to (?:visit|go to|plan a trip))\s+([a-zA-Z\s]+)",
        "template": "get_best_time_visit_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:entry fee|ticket|cost|price).*(?:for|of)\s+([a-zA-Z\s]+)",
        "template": "get_place_entry_fee",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:opening hours|timing|when does it open|open hours).*(?:of|for)\s+(.+)",
        "template": "get_place_hours", 
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|describe|info on|details of)\s+(.+) (?:fort|temple|museum|place|monument|attraction)",
        "template": "get_place_description",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|describe|info on|details of)\s+(.+)",
        "template": "get_place_description",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    
    # Emergency
    {
        "pattern": r"(hospitals?|pharmacies|police stations?|police|clinics?|doctors?).*(?:in|at|near|around)\s+(.+)",
        "template": "list_services_in_district",
        "extractor": lambda m: {"service_type": singularize(m.group(1)), "district": m.group(2).strip("?.! ")}
    },
    {
        "pattern": r"(?:where can i (?:get|find)|i need).*(?:medical|health|doctor|hospital|police|emergency).*(?:in|at|near|around)\s+(\w+)",
        "template": "list_services_in_district",
        "extractor": lambda m: {"service_type": "Hospital", "district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"emergency.*(?:contact|number|phone|helpline).*(?:for|of|in)\s+(.+)",
        "template": "get_service_contact",
        "extractor": lambda m: {"name": m.group(1).strip("?.! ")}
    },
    
    # Businesses
    {
        "pattern": r"(hotels?|restaurants?|taxis?|lodges?|homestays?|resorts?|cafes?).*(?:in|at|near|around)\s+(.+)",
        "template": "list_businesses_in_district",
        "extractor": lambda m: {"category": singularize(m.group(1)), "district": m.group(2).strip("?.! ")}
    },
    {
        "pattern": r"(?:where (?:can i|to)|suggest|recommend).*(?:eat|dine|food|lunch|dinner|breakfast).*(?:in|at|near|around)\s+(\w+)",
        "template": "list_businesses_in_district",
        "extractor": lambda m: {"category": "Restaurant", "district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:where (?:can i|to)|suggest|recommend).*(?:stay|sleep|hotel|lodge|resort|accommodation).*(?:in|at|near|around)\s+(\w+)",
        "template": "list_businesses_in_district",
        "extractor": lambda m: {"category": "Hotel", "district": m.group(1).strip("?.! ")}
    },
     {
        "pattern": r"(?:contact|phone).*(?:number|details).*(?:for|of)\s+(.+)",
        "template": "get_business_contact",
        "extractor": lambda m: {"name": m.group(1).strip("?.! ")}
    },
    # CRITICAL FIX: Explicit pattern for "Show me all tourist places"
    {
        "pattern": r"(?:show|list|give|find|tell).+(?:me|us)?.+(?:all|every).+tourist places?",
        "template": "list_all_places",
        "params": {"limit": 20}
    },
    
    # NEW: Analytics patterns
    {
        "pattern": r"(?:which|what).+district.+(?:most|highest|maximum).+places?",
        "template": "district_with_most_places",
        "params": {}
    },
    {
        "pattern": r"district.+(?:most|maximum).+tourist",
        "template": "district_with_most_places",
        "params": {}
    },
    {
        "pattern": r"(?:which|what).+districts?.+(?:have|with).+places?",
        "template": "districts_with_places",
        "params": {}
    },
    {
        "pattern": r"(?:show|list).+districts?.+tourist",
        "template": "districts_with_places",
        "params": {}
    },
    
    {
        "pattern": r"(?:how many|count|total).+business",
        "template": "count_all_businesses",
        "params": {}
    },
    {
        "pattern": r"(?:show|list|give|find).+(?:all|every).+business",
        "template": "list_all_businesses",
        "params": {"limit": 10}
    },
]

def get_sql_from_template(query: str) -> Optional[str]:
    """
    Try to match query to a template.
    Returns SQL string if match found, None otherwise.
    """
    query_lower = query.lower()
    
    for pattern_config in QUERY_PATTERNS:
        match = re.search(pattern_config["pattern"], query_lower, re.IGNORECASE)
        
        if match:
            template_name = pattern_config["template"]
            template = SQL_TEMPLATES[template_name]
            
            # Extract parameters
            if "extractor" in pattern_config:
                try:
                    params = pattern_config["extractor"](match)
                except Exception:
                    # If extraction fails, skip this pattern
                    continue
            else:
                params = pattern_config.get("params", {})
            
            # Substitute parameters
            sql = template.format(**params)
            
            print(f"✅ SQL Template Cache HIT: {template_name}")
            return sql.strip()
    
    print(f"❌ SQL Template Cache MISS: Falling back to LLM generation")
    return None
