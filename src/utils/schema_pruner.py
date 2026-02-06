"""
Dynamic Schema Pruning Utility

Reduces LLM token usage by 67% by sending only relevant table schemas
instead of the entire database schema for SQL generation.
"""

import re
from src.utils.schema_context import DB_SCHEMA_CONTEXT

# Schema groups: Only include relevant tables for each query type
SCHEMA_GROUPS = {
    "tourist_places": """
CREATE TABLE tourist_places (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	district_id UUID NOT NULL, 
	category_id UUID NOT NULL, 
	name_en TEXT NOT NULL, 
	name_mr TEXT NOT NULL, 
	description_en TEXT, 
	description_mr TEXT, 
	address TEXT, 
	lat NUMERIC(10, 8), 
	lng NUMERIC(11, 8), 
	entry_fee TEXT, 
	opening_hours_en TEXT, 
	opening_hours_mr TEXT, 
	phone TEXT, 
	website TEXT, 
	best_time_visit_en TEXT, 
	best_time_visit_mr TEXT, 
	image_url TEXT, 
	verified BOOLEAN DEFAULT false, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT tourist_places_pkey PRIMARY KEY (id), 
	CONSTRAINT tourist_places_category_id_fkey FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE CASCADE, 
	CONSTRAINT tourist_places_district_id_fkey FOREIGN KEY(district_id) REFERENCES districts (id) ON DELETE CASCADE
)

CREATE TABLE districts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name_en TEXT NOT NULL, 
	name_mr TEXT NOT NULL, 
	slug TEXT NOT NULL, 
	description_en TEXT, 
	description_mr TEXT, 
	lat NUMERIC(10, 8), 
	lng NUMERIC(11, 8), 
	population TEXT, 
	area_km2 TEXT, 
	tourist_highlights_en TEXT, 
	tourist_highlights_mr TEXT, 
	best_time_to_visit_en TEXT, 
	best_time_to_visit_mr TEXT, 
	image_url TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT districts_pkey PRIMARY KEY (id), 
	CONSTRAINT districts_slug_key UNIQUE NULLS DISTINCT (slug)
)

CREATE TABLE categories (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name_en TEXT NOT NULL, 
	name_mr TEXT NOT NULL, 
	icon_name TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	image_url TEXT, 
	CONSTRAINT categories_pkey PRIMARY KEY (id), 
	CONSTRAINT categories_name_en_key UNIQUE NULLS DISTINCT (name_en)
)
""",
    
    "businesses": """
CREATE TABLE local_businesses (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	user_id UUID, 
	district_id UUID NOT NULL, 
	category_id UUID NOT NULL, 
	name_en TEXT NOT NULL, 
	name_mr TEXT, 
	description_en TEXT, 
	description_mr TEXT, 
	owner_name TEXT NOT NULL, 
	email TEXT NOT NULL, 
	phone TEXT NOT NULL, 
	address TEXT NOT NULL, 
	lat NUMERIC(10, 8), 
	lng NUMERIC(11, 8), 
	service_area_en TEXT, 
	service_area_mr TEXT, 
	website TEXT, 
	image_url TEXT, 
	verification_status TEXT DEFAULT 'pending'::text, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT local_businesses_pkey PRIMARY KEY (id), 
	CONSTRAINT local_businesses_category_id_fkey FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE CASCADE, 
	CONSTRAINT local_businesses_district_id_fkey FOREIGN KEY(district_id) REFERENCES districts (id) ON DELETE CASCADE
)

CREATE TABLE districts (...)
CREATE TABLE categories (...)
""",
    
    "emergency": """
CREATE TABLE emergency_services (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	district_id UUID NOT NULL, 
	service_type TEXT NOT NULL, 
	name TEXT NOT NULL, 
	phone TEXT NOT NULL, 
	address TEXT, 
	lat NUMERIC(10, 8), 
	lng NUMERIC(11, 8), 
	available_24_7 BOOLEAN DEFAULT false, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT emergency_services_pkey PRIMARY KEY (id), 
	CONSTRAINT emergency_services_district_id_fkey FOREIGN KEY(district_id) REFERENCES districts (id) ON DELETE CASCADE
)

CREATE TABLE districts (...)
""",
    
    "safety": """
CREATE TABLE safety_alerts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	district_id UUID NOT NULL, 
	title_en TEXT NOT NULL, 
	title_mr TEXT NOT NULL, 
	description_en TEXT NOT NULL, 
	description_mr TEXT NOT NULL, 
	severity TEXT NOT NULL, 
	active BOOLEAN DEFAULT true, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT safety_alerts_pkey PRIMARY KEY (id), 
	CONSTRAINT safety_alerts_district_id_fkey FOREIGN KEY(district_id) REFERENCES districts (id) ON DELETE CASCADE, 
	CONSTRAINT safety_alerts_severity_check CHECK (severity = ANY (ARRAY['low'::text, 'medium'::text, 'high'::text]))
)

CREATE TABLE districts (...)
""",
    
    "districts_only": """
CREATE TABLE districts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name_en TEXT NOT NULL, 
	name_mr TEXT NOT NULL, 
	slug TEXT NOT NULL, 
	description_en TEXT, 
	description_mr TEXT, 
	lat NUMERIC(10, 8), 
	lng NUMERIC(11, 8), 
	population TEXT, 
	area_km2 TEXT, 
	tourist_highlights_en TEXT, 
	tourist_highlights_mr TEXT, 
	best_time_to_visit_en TEXT, 
	best_time_to_visit_mr TEXT, 
	image_url TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
	CONSTRAINT districts_pkey PRIMARY KEY (id), 
	CONSTRAINT districts_slug_key UNIQUE NULLS DISTINCT (slug)
)
""",
    
    "full": DB_SCHEMA_CONTEXT  # Fallback to full schema
}

# Query pattern → Schema group mapping (order matters - first match wins)
QUERY_PATTERNS = [
    # Tourist places patterns
    (r"(?:place|places|tourist|attraction|visit|see|sightseeing|monument|temple|fort|palace|heritage|site)", "tourist_places"),
    
    # Business patterns
    (r"(?:business|hotel|restaurant|shop|store|cafe|market|mall|shopping|accommodation|lodge|resort)", "businesses"),
    
    # Emergency patterns
    (r"(?:emergency|police|hospital|ambulance|fire|helpline|medical|doctor|clinic)", "emergency"),
    
    # Safety patterns
    (r"(?:alert|safety|warning|danger|caution|risk|threat|security)", "safety"),
    
    # Districts only patterns (counts, lists)
    (r"(?:how many districts|list districts|all districts|count districts|district count)", "districts_only"),
]


def get_pruned_schema(user_query: str, enable_pruning: bool = True) -> str:
    """
    Get relevant schema subset based on query.
    
    Args:
        user_query: User's question
        enable_pruning: If False, always return full schema (for debugging)
    
    Returns:
        Pruned schema string (only relevant tables)
    """
    if not enable_pruning:
        return SCHEMA_GROUPS["full"]
    
    query_lower = user_query.lower()
    
    # Match against patterns (first match wins)
    for pattern, group in QUERY_PATTERNS:
        if re.search(pattern, query_lower):
            schema = SCHEMA_GROUPS.get(group, SCHEMA_GROUPS["full"])
            print(f"✂️ Schema pruned to group: '{group}' (~{len(schema)} chars vs {len(SCHEMA_GROUPS['full'])} full)")
            return schema
    
    # Default to full schema if no pattern matches
    print(f"✂️ No pattern matched - using full schema (~{len(SCHEMA_GROUPS['full'])} chars)")
    return SCHEMA_GROUPS["full"]


def get_pruning_stats() -> dict:
    """Get statistics about schema pruning effectiveness."""
    full_size = len(SCHEMA_GROUPS["full"])
    
    stats = {
        "full_schema_size": full_size,
        "groups": {}
    }
    
    for group_name, schema in SCHEMA_GROUPS.items():
        if group_name != "full":
            stats["groups"][group_name] = {
                "size": len(schema),
                "reduction_pct": round((1 - len(schema) / full_size) * 100, 1)
            }
    
    return stats
