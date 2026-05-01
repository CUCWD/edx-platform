#!/usr/bin/env python
"""
Quick test to verify estimated_time fields are accessible on XBlocks
Run this with: tutor dev run cms python test_estimated_time_backend.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms.settings.test')

django.setup()

from xmodule.modulestore import modulestore

# Get a test course
try:
    # List all courses
    ms = modulestore()
    courses = list(ms.get_courses())
    
    print(f"\nTotal courses found: {len(courses)}")
    
    if courses:
        course = courses[0]
        print(f"\n✓ Found course: {course.id}")
        
        # Get all blocks in the course
        all_blocks = list(ms.get_items(course.location.course_key))
        
        print(f"Total blocks in course: {len(all_blocks)}")
        
        for i, block in enumerate(all_blocks[:5]):  # Check first 5 blocks
            print(f"\n--- Block {i+1}: {block.display_name} ({block.category}) ---")
            print(f"    Location: {block.location}")
            
            # Check if fields exist
            has_estimated_time = hasattr(block, 'estimated_time')
            has_show_estimated_time = hasattr(block, 'show_estimated_time')
            has_override_estimated_time = hasattr(block, 'override_estimated_time')
            
            print(f"    Has estimated_time: {has_estimated_time}")
            print(f"    Has show_estimated_time: {has_show_estimated_time}")
            print(f"    Has override_estimated_time: {has_override_estimated_time}")
            
            if has_estimated_time:
                try:
                    val = block.estimated_time
                    print(f"    estimated_time value: {val} (type: {type(val).__name__})")
                except Exception as e:
                    print(f"    Error reading estimated_time: {e}")
                    
            if has_show_estimated_time:
                try:
                    val = block.show_estimated_time
                    print(f"    show_estimated_time value: {val}")
                except Exception as e:
                    print(f"    Error reading show_estimated_time: {e}")
                    
            if has_override_estimated_time:
                try:
                    val = block.override_estimated_time
                    print(f"    override_estimated_time value: {val}")
                except Exception as e:
                    print(f"    Error reading override_estimated_time: {e}")
    else:
        print("✗ No courses found. Create a course first.")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
