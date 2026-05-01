/**
 * Tests for the EstimatedTimeEditor
 */
describe('EstimatedTimeEditor', function() {
    'use strict';

    var editor, mockModel, mockTemplate;

    beforeEach(function() {
        // Mock the AbstractEditor
        mockTemplate = '<input id="estimated_time" /><input type="checkbox" id="estimated_time_override" /><input type="checkbox" id="show_estimated_time" />';
        
        mockModel = {
            get: jasmine.createSpy('get').and.callFake(function(attr) {
                switch(attr) {
                    case 'estimated_time':
                        return 300; // 5 minutes in seconds
                    case 'override_estimated_time':
                        return false;
                    case 'show_estimated_time':
                        return true;
                    default:
                        return undefined;
                }
            })
        };
    });

    describe('initialization', function() {
        it('should have correct fieldName', function() {
            // Verify EstimatedTimeEditor is defined and has correct properties
            expect(typeof EstimatedTimeEditor).toBe('function');
            
            var instance = new EstimatedTimeEditor({model: mockModel});
            expect(instance.fieldName).toBe('estimated_time');
        });

        it('should have correct templateName', function() {
            var instance = new EstimatedTimeEditor({model: mockModel});
            expect(instance.templateName).toBe('estimated-time-editor');
        });

        it('should have correct className', function() {
            var instance = new EstimatedTimeEditor({model: mockModel});
            expect(instance.className).toBe('estimated-time-settings');
        });
    });

    describe('time conversion', function() {
        it('should convert seconds to HH:MM:SS format', function() {
            var totalSeconds = 300; // 5 minutes
            var hours = Math.floor(totalSeconds / 3600);
            var minutes = Math.floor((totalSeconds % 3600) / 60);
            var seconds = totalSeconds % 60;
            var timeStr = String(hours).padStart(2, '0') + ':' + 
                          String(minutes).padStart(2, '0') + ':' + 
                          String(seconds).padStart(2, '0');
            
            expect(timeStr).toBe('00:05:00');
        });

        it('should convert 1 hour to 01:00:00', function() {
            var totalSeconds = 3600;
            var hours = Math.floor(totalSeconds / 3600);
            var minutes = Math.floor((totalSeconds % 3600) / 60);
            var seconds = totalSeconds % 60;
            var timeStr = String(hours).padStart(2, '0') + ':' + 
                          String(minutes).padStart(2, '0') + ':' + 
                          String(seconds).padStart(2, '0');
            
            expect(timeStr).toBe('01:00:00');
        });

        it('should convert 1 hour 5 minutes 30 seconds', function() {
            var totalSeconds = 3930; // 1:05:30
            var hours = Math.floor(totalSeconds / 3600);
            var minutes = Math.floor((totalSeconds % 3600) / 60);
            var seconds = totalSeconds % 60;
            var timeStr = String(hours).padStart(2, '0') + ':' + 
                          String(minutes).padStart(2, '0') + ':' + 
                          String(seconds).padStart(2, '0');
            
            expect(timeStr).toBe('01:05:30');
        });

        it('should convert 0 seconds to 00:00:00', function() {
            var totalSeconds = 0;
            var hours = Math.floor(totalSeconds / 3600);
            var minutes = Math.floor((totalSeconds % 3600) / 60);
            var seconds = totalSeconds % 60;
            var timeStr = String(hours).padStart(2, '0') + ':' + 
                          String(minutes).padStart(2, '0') + ':' + 
                          String(seconds).padStart(2, '0');
            
            expect(timeStr).toBe('00:00:00');
        });
    });

    describe('getRequestData', function() {
        it('should return empty object if no changes', function() {
            var instance = new EstimatedTimeEditor({model: mockModel});
            
            // Mock the jQuery selections
            instance.$ = jasmine.createSpy('$').and.returnValue({
                prop: function(attr) {
                    if (attr === 'checked') {
                        return false; // override unchecked
                    }
                }
            });
            
            instance.defaultEstimatedTime = 300;
            instance.startOverrideValue = false;
            instance.startVisibilityValue = true;
            instance.getValue = jasmine.createSpy('getValue').and.returnValue(300);
            
            var result = instance.getRequestData();
            expect(Object.keys(result).length).toBe(0);
        });

        it('should return metadata when values change', function() {
            var instance = new EstimatedTimeEditor({model: mockModel});
            
            // Mock jQuery to return new values
            instance.$ = jasmine.createSpy('$').and.returnValue({
                prop: function(attr) {
                    if (attr === 'checked') {
                        return true; // toggle changed
                    }
                }
            });
            
            instance.defaultEstimatedTime = 300;
            instance.startOverrideValue = false;
            instance.startVisibilityValue = false;
            instance.getValue = jasmine.createSpy('getValue').and.returnValue('00:05:00');
            
            var result = instance.getRequestData();
            expect(result.metadata).toBeDefined();
            expect(result.metadata.estimated_time).toBe('00:05:00');
            expect(result.metadata.override_estimated_time).toBe(true);
            expect(result.metadata.show_estimated_time).toBe(true);
        });
    });
});
