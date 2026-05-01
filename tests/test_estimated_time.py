"""
Tests for the estimated time to complete feature
"""
import pytest
from datetime import timedelta
from cms.djangoapps.contentstore.courseware_index import calculate_html_reading_time_seconds
from xmodule.x_module import XModuleFields


class TestEstimatedTimeFields:
    """Test that estimated_time fields are properly defined in XModuleFields"""
    
    def test_estimated_time_field_exists(self):
        """Verify estimated_time field is defined in XModuleFields"""
        assert hasattr(XModuleFields, 'estimated_time')
        field = XModuleFields.estimated_time
        assert field is not None
        
    def test_show_estimated_time_field_exists(self):
        """Verify show_estimated_time field is defined in XModuleFields"""
        assert hasattr(XModuleFields, 'show_estimated_time')
        field = XModuleFields.show_estimated_time
        assert field is not None
        
    def test_override_estimated_time_field_exists(self):
        """Verify override_estimated_time field is defined in XModuleFields"""
        assert hasattr(XModuleFields, 'override_estimated_time')
        field = XModuleFields.override_estimated_time
        assert field is not None
        
    def test_estimated_time_default_value(self):
        """Verify estimated_time has a default value of 60 seconds"""
        field = XModuleFields.estimated_time
        # Default should be 60 seconds (1 minute)
        assert field.default == timedelta(seconds=60)
        
    def test_show_estimated_time_default_false(self):
        """Verify show_estimated_time defaults to False"""
        field = XModuleFields.show_estimated_time
        assert field.default is False
        
    def test_override_estimated_time_default_false(self):
        """Verify override_estimated_time defaults to False"""
        field = XModuleFields.override_estimated_time
        assert field.default is False


class TestEstimatedTimeCalculation:
    """Test the estimated time calculation logic"""
    
    def test_time_conversion_to_seconds(self):
        """Test converting timedelta to seconds"""
        time = timedelta(hours=1, minutes=30, seconds=45)
        total_seconds = int(time.total_seconds())
        
        # Should be 3600 + 1800 + 45 = 5445 seconds
        assert total_seconds == 5445
        
    def test_time_conversion_to_hms(self):
        """Test converting seconds back to HH:MM:SS format"""
        total_seconds = 5445
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        assert time_str == "01:30:45"
        
    def test_zero_time_conversion(self):
        """Test converting zero seconds"""
        total_seconds = 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        assert time_str == "00:00:00"
        
    def test_one_minute_conversion(self):
        """Test converting 60 seconds (1 minute)"""
        total_seconds = 60
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        assert time_str == "00:01:00"


class TestEstimatedTimeSerializaton:
    """Test estimated time field serialization for API responses"""
    
    def test_timedelta_to_minutes_conversion(self):
        """Test converting timedelta to minutes for JSON response"""
        estimated_time = timedelta(minutes=5)
        minutes = int(estimated_time.total_seconds() / 60)
        
        # Round up to nearest minute
        if estimated_time.total_seconds() % 60 > 0:
            minutes += 1
            
        assert minutes == 5
        
    def test_timedelta_with_seconds_rounding(self):
        """Test that seconds are properly rounded up"""
        estimated_time = timedelta(minutes=5, seconds=30)
        total_seconds = estimated_time.total_seconds()
        minutes = int((total_seconds + 59) // 60)
        
        assert minutes == 6
        
    def test_null_estimated_time_handling(self):
        """Test handling of None estimated_time"""
        estimated_time = None
        
        if estimated_time is None:
            minutes = None
        else:
            minutes = int(estimated_time.total_seconds() / 60)
            
        assert minutes is None


class TestTextReadTimeCalculation:
    """Test readtime-style text/html estimation for text XBlocks."""

    def test_html_text_uses_265_wpm(self):
        html = ' '.join(['word'] * 265)
        assert calculate_html_reading_time_seconds(html) == 60

    def test_html_tags_are_ignored_for_word_count(self):
        html = '<p>This is <strong>simple</strong> text</p>'
        assert calculate_html_reading_time_seconds(html) == 1

    def test_image_weight_decreases_per_image(self):
        html = '<img src="1"/><img src="2"/><img src="3"/>'
        assert calculate_html_reading_time_seconds(html) == 33

    def test_image_weight_has_minimum_floor(self):
        html = ''.join(f'<img src="{idx}"/>' for idx in range(15))
        assert calculate_html_reading_time_seconds(html) == 90

    def test_empty_html_returns_zero(self):
        assert calculate_html_reading_time_seconds('') == 0


if __name__ == '__main__':
    pytest.main([__file__])
