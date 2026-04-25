from __future__ import annotations

import sys
sys.path.insert(0, '.')

from utils.supabase_rest import SupabaseRestClient

client = SupabaseRestClient()
rows = client.select('sources', 'id,name,type')
print(rows[:5])
