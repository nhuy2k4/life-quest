"""update people quest labels

Revision ID: 0057_update_people_quest_labels
Revises: 0056_add_poi_id_to_event_quests
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa
import json

revision = '0057_update_people_quest_labels'
down_revision = '0056_add_poi_id_to_event_quests'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Update the labels and label_rules of the "People shot" quest (UUID: a65f6494-33a0-413b-9f67-c89306f2b08d)
    new_labels = [
        "person", "people", "human", "face", "head", "portrait", 
        "man", "woman", "smile", "cheek", "chin", "forehead", 
        "nose", "lips", "eyebrow", "eyewear", "glasses", "selfie", 
        "hair", "hairstyle"
    ]
    new_label_rules = {l: 0.55 for l in new_labels}
    
    # Format JSON strings properly for SQLite
    labels_str = json.dumps(new_labels)
    rules_str = json.dumps(new_label_rules)
    
    # SQLite requires escaping single quotes by doubling them if any, but our JSON key/values only use double quotes.
    op.execute(
        f"UPDATE quests SET labels = '{labels_str}', label_rules = '{rules_str}' WHERE id = 'a65f6494-33a0-413b-9f67-c89306f2b08d'"
    )

def downgrade() -> None:
    old_labels = ["person", "people", "human"]
    old_label_rules = {"person": 0.55, "people": 0.55, "human": 0.55}
    
    labels_str = json.dumps(old_labels)
    rules_str = json.dumps(old_label_rules)
    
    op.execute(
        f"UPDATE quests SET labels = '{labels_str}', label_rules = '{rules_str}' WHERE id = 'a65f6494-33a0-413b-9f67-c89306f2b08d'"
    )
