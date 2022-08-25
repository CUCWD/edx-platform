 
    // function that hides <fields_to_show> by default and shows it when
    // <field_to_change> value is set to <value>
    function RegistrationChange(field_to_change, field_to_show, value){
        field_to_change = document.querySelector(field_to_change);
        field_to_show = document.querySelector(field_to_show);
        
        const initialDisplay = field_to_change.style.display;
        field_to_show.style.display = "none";

        field_to_show.required = false;
        
        var DEFAULT_HIDDEN_VALUE = "N/A";
        var DEFAULT_VISIBLE_VALUE = '';
        
        
        var default_value_field = field_to_show.querySelector("input");

        if(default_value_field == null){
            default_value_field = field_to_show.querySelector("select");
            DEFAULT_HIDDEN_VALUE = "prefer-not-to-say";            
        }

        default_value_field.value = DEFAULT_HIDDEN_VALUE;

        field_to_change.addEventListener("change", function(event) {     
            if(event.target.value == value){
                field_to_show.style.display = initialDisplay;
                default_value_field.value = DEFAULT_VISIBLE_VALUE;
            }
            else{
                field_to_show.style.display = "none";
                default_value_field.value = DEFAULT_HIDDEN_VALUE; 
            }

        });
    }
    
    RegistrationChange('.select-enrolled_in_school', '.select-enrolled_in_school_type', "yes");
    RegistrationChange('.select-ethnicity', '.text-ethnicity_free_input', "other");
    RegistrationChange('.select-gender', '.text-gender_free_input', "o");



