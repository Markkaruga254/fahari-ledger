Alembic migrations go here once the schema stabilizes.

For the hackathon build, tables are created directly with
`Base.metadata.create_all(engine)` (see `scripts/seed_demo_data.py`) to move
fast. Wire up `alembic init` here post-hackathon if the project continues.
