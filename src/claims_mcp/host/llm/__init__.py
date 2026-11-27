"""LLM access behind an adapter: neutral types, the adapter base class and its implementations.

The agent loop only uses these types and ChatModelAdapterBase, never a provider SDK, so a new
provider means one new adapter class.
"""
