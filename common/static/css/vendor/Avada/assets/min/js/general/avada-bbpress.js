jQuery(window).load(function(){jQuery(".bbp-template-notice").each(function(){var a="",b="";jQuery(this).hasClass("info")?(jQuery(this).attr("class","fusion-alert alert notice alert-info"),b="fa-info-circle"):(jQuery(this).attr("class","fusion-alert alert notice alert-warning"),b="fa-cog"),jQuery(this).addClass("fusion-alert-"+avadaBbpressVars.alert_box_text_align),"capitalize"===avadaBbpressVars.alert_box_text_transform&&jQuery(this).addClass("fusion-alert-capitalize"),"yes"===avadaBbpressVars.alert_box_dismissable&&(jQuery(this).addClass("alert-dismissable"),a='<button class="close toggle-alert" aria-hidden="true" data-dismiss="alert" type="button">&times;</button>'),"yes"===avadaBbpressVars.alert_box_shadow&&jQuery(this).addClass("alert-shadow"),jQuery(this).css("border-width",parseInt(avadaBbpressVars.alert_border_size)+"px"),jQuery(this).children("tt").contents().unwrap(),jQuery(this).children("p").contents().unwrap(),a+='<div class="fusion-alert-content-wrapper"><span class="alert-icon"><i class="fa-lg fa '+b+'"></i></span><span class="fusion-alert-content">'+jQuery(this).html()+"</span>",jQuery(this).html(a),jQuery(this).children(".close").click(function(a){a.preventDefault(),jQuery(this).parent().slideUp()})}),jQuery(".bbp-login-form").each(function(){jQuery(this).children("tt").contents().unwrap()})});