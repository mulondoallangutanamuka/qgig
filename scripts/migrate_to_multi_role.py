"""
Migration script to backfill existing users into the new multi-role architecture.

This script:
1. Creates roles (professional, institution, admin) if they don't exist
2. Migrates existing users.role into user_roles assignments
3. Creates missing profile records (professional/institution) for all users
4. Preserves all existing data and relationships
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.professional import Professional
from app.models.institution import Institution
from app.models.role import Role, UserRoleAssignment
from sqlalchemy.exc import IntegrityError


def migrate_to_multi_role():
    """Main migration function"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("QGIG MULTI-ROLE MIGRATION")
        print("=" * 60)
        print()
        
        # Step 1: Create roles if they don't exist
        print("Step 1: Creating roles...")
        roles_data = [
            ('professional', True),
            ('institution', True),
            ('admin', False)  # Admin is not switchable
        ]
        
        role_map = {}
        for role_name, is_switchable in roles_data:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, is_switchable=is_switchable)
                db.add(role)
                db.flush()
                print(f"  ✓ Created role: {role_name}")
            else:
                print(f"  ✓ Role exists: {role_name}")
            role_map[role_name] = role
        
        db.commit()
        print()
        
        # Step 2: Get all users
        print("Step 2: Processing users...")
        users = db.query(User).all()
        print(f"  Found {len(users)} users")
        print()
        
        migrated_count = 0
        skipped_count = 0
        
        for user in users:
            print(f"Processing user: {user.email} (ID: {user.id}, Role: {user.role.value})")
            
            # Step 3: Assign roles based on existing user.role
            if user.role == UserRole.ADMIN:
                # Admin gets only admin role
                roles_to_assign = ['admin']
            else:
                # Non-admin users get both professional and institution roles
                roles_to_assign = ['professional', 'institution']
            
            for role_name in roles_to_assign:
                role = role_map[role_name]
                
                # Check if assignment already exists
                existing = db.query(UserRoleAssignment).filter(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role_id == role.id
                ).first()
                
                if not existing:
                    assignment = UserRoleAssignment(user_id=user.id, role_id=role.id)
                    db.add(assignment)
                    print(f"  ✓ Assigned role: {role_name}")
                else:
                    print(f"  - Role already assigned: {role_name}")
            
            # Step 4: Create missing profiles
            if user.role != UserRole.ADMIN:
                # Ensure professional profile exists
                prof = db.query(Professional).filter(Professional.user_id == user.id).first()
                if not prof:
                    prof = Professional(user_id=user.id)
                    db.add(prof)
                    print(f"  ✓ Created professional profile")
                else:
                    print(f"  - Professional profile exists")
                
                # Ensure institution profile exists
                inst = db.query(Institution).filter(Institution.user_id == user.id).first()
                if not inst:
                    inst = Institution(user_id=user.id)
                    db.add(inst)
                    print(f"  ✓ Created institution profile")
                else:
                    print(f"  - Institution profile exists")
            
            migrated_count += 1
            print()
        
        # Commit all changes
        db.commit()
        
        print("=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"✓ Processed {migrated_count} users")
        print(f"✓ All users now have multi-role support")
        print(f"✓ Non-admin users can switch between Professional and Institution")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print("MIGRATION FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print()
    response = input("This will migrate all users to the new multi-role system. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_to_multi_role()
    else:
        print("Migration cancelled.")
