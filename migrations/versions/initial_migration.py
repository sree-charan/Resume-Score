"""Initial database migration

Revision ID: initial_migration
Create Date: 2024-03-15 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create job_descriptions table
    op.create_table(
        'job_descriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255)),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('path', sa.String(512), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False)
    )

    # Create resumes table with all fields
    op.create_table(
        'resumes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('path', sa.String(512), nullable=False),
        sa.Column('job_description_id', sa.String(36), sa.ForeignKey('job_descriptions.id'), nullable=False),
        
        # Basic Information
        sa.Column('candidate_name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('location', sa.String(255)),
        
        # Online Presence
        sa.Column('linkedin_url', sa.String(255)),
        sa.Column('github_url', sa.String(255)),
        sa.Column('portfolio_url', sa.String(255)),
        sa.Column('other_urls', sa.Text),
        
        # Skills and Expertise
        sa.Column('skills', sa.Text),
        sa.Column('languages', sa.Text),
        sa.Column('certifications', sa.Text),
        
        # Education
        sa.Column('education', sa.Text),
        sa.Column('gpa', sa.Float),
        sa.Column('academic_awards', sa.Text),
        
        # Work Experience
        sa.Column('experience', sa.Text),
        sa.Column('total_years_experience', sa.Float),
        sa.Column('current_position', sa.String(255)),
        sa.Column('current_company', sa.String(255)),
        
        # Research and Publications
        sa.Column('research_papers', sa.Text),
        sa.Column('publications', sa.Text),
        sa.Column('patents', sa.Text),
        
        # Projects
        sa.Column('projects', sa.Text),
        
        # Leadership and Activities
        sa.Column('leadership_roles', sa.Text),
        sa.Column('volunteer_work', sa.Text),
        sa.Column('extracurricular', sa.Text),
        
        # Personal
        sa.Column('interests', sa.Text),
        sa.Column('achievements', sa.Text),
        
        # Analysis results
        sa.Column('score', sa.Float, default=0.0),
        sa.Column('detailed_analysis', sa.Text),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )

def downgrade():
    op.drop_table('resumes')
    op.drop_table('job_descriptions')